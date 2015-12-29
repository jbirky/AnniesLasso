
"""
Perform the 17-label training for a few Lambda parameters for the red giant
branch sample.
"""

import cPickle as pickle
import numpy as np
import os
from sys import maxsize
from astropy.table import Table

import AnniesLasso as tc

np.random.seed(123) # For reproducibility.

from time import time
# Some "configurable" opions..
threads = 1
mod = 10

# Data.
PATH, CATALOG, FILE_FORMAT = ("/Users/arc/research/apogee", "apogee-rg.fits",
    "apogee-rg-{}.memmap")

# Load the data.
labelled_set = Table.read(os.path.join(PATH, CATALOG))
dispersion = np.memmap(os.path.join(PATH, FILE_FORMAT).format("dispersion"),
    mode="r", dtype=float)
normalized_flux = np.memmap(
    os.path.join(PATH, FILE_FORMAT).format("normalized-flux"),
    mode="r", dtype=float).reshape((len(labelled_set), -1))
normalized_ivar = np.memmap(
    os.path.join(PATH, FILE_FORMAT).format("normalized-ivar"),
    mode="r", dtype=float).reshape(normalized_flux.shape)

#normalized_flux = normalized_flux[:, :2000]
#normalized_ivar = normalized_ivar[:, :2000]
#dispersion = dispersion[:2000]

elements = [label_name for label_name in labelled_set.dtype.names \
    if label_name not in ("PARAM_M_H", "SRC_H") and label_name.endswith("_H")]

# Split up the data into ten random subsets.
q = np.random.randint(0, maxsize, len(labelled_set)) % mod

validate_set = (q == 0)
test_set = (q == (mod - 1))
train_set = (~validate_set) * (~test_set)
assert np.sum(np.hstack([validate_set, test_set, train_set])) == q.size

# Create a vectorizer for all models.
vectorizer = tc.vectorizer.NormalizedPolynomialVectorizer(labelled_set,
    tc.vectorizer.polynomial.terminator(["TEFF", "LOGG", "FE_H"], 2))


# Create a regularized Cannon model to try at different Lambda values.
regularized_cannon = tc.L1RegularizedCannonModel(labelled_set[train_set],
    normalized_flux[train_set], normalized_ivar[train_set],
    dispersion=dispersion, threads=threads)
regularized_cannon.vectorizer = vectorizer
regularized_cannon.s2 = 0.0


# For ~50 pixels, try some Lambda values.
# Recommended pixels from Melissa, in vacuum.
wavelengths = [
    16795.77313988085, # --> continuum
    15339.0, # --> Teff sensitivity
    15720,   # --> Teff sensitivity
    15770,   # --> logg sensitivity
    16811.5, # --> Logg sensitivity
    15221.5, # --> [Fe/H] sensitivity
    16369,   # --> [alpha/Fe] sensitivity
]

# These lines were all given in air, so I have converted them to vacuum.
# Three Fe I lines from Smith et al. (2013)
# Air: 15490.339, 15648.510, 15964.867
# Vac: [15494.571901901722, 15652.785921456885, 15969.22897071544]
wavelengths.extend(
    [15494.571901901722, 15652.785921456885, 15969.22897071544])

# Two Mg I lines from Smith et al. (2013)
# Air: 15765.8, 15879.5
# Vac: [15770.107823467057, 15883.838750072413]
wavelengths.extend(
    [15770.107823467057, 15883.838750072413])

# Two Al I lines from Smith et al. (2013)
# Air: 16718.957, 16763.359
# Vac: [16723.524113765838, 16767.938194147067]
wavelengths.extend(
    [16723.524113765838, 16767.938194147067])

# Two Si II lines from Smith et al. (2013)
# Air: 15960.063, 16060.009
# Vac: [15964.42366396639, 16064.396850911658]
wavelengths.extend(
    [15964.42366396639, 16064.396850911658])

# Two Ca I lines from Smith et al. (2013)
# Air: 16150.763, 16155.236
# Vac: [16155.17553813612, 16159.649754913306]
wavelengths.extend(
    [16155.17553813612, 16159.649754913306])

# Two Cr I lines from Smith et al. (2013)
# Air: 15680.063, 15860.214
# Vac: [15684.347503529489, 15864.547504173868]
wavelengths.extend(
    [15684.347503529489, 15864.547504173868])

# One Co I line from Smith et al. (2013)
# Air: 16757.7
# Vac: 16762.27765450469
wavelengths.extend(
    [16762.27765450469])

# One V I line from Smith et al. (2013) 
# Air: 15924.
# Vac: 15928.350854428922
wavelengths.extend(
    [15928.350854428922])
    
# Two Ni I lines from Smith et al. (2013)
# Air: 16589.295, 16673.711
# Vac: [16593.826837590106, 16678.26580389432]
wavelengths.extend(
    [16593.826837590106, 16678.26580389432])

# Two K I line from Smith et al. (2013)
# Air: 15163.067,15168.376
# Vac: [15167.21089680259, 15172.521340566429]
wavelengths.extend(
    [15167.21089680259, 15172.521340566429])

# Two Mn I lines from Smith et al. (2013)
# Air: 15217., 15262.
# Vac:  [15221.158563809242, 15266.17080169663]
wavelengths.extend(
     [15221.158563809242, 15266.17080169663])


# Set the model up for validation.
Lambdas = 10**np.hstack([[0, 1, 2], np.arange(3, 6, 0.2)])
pixel_mask = np.searchsorted(dispersion, wavelengths)


"""
filename = "convexity-proof-3label-all.pkl"
if not os.path.exists(filename):
    regularizations, chi_sq, log_det, all_models = \
        regularized_cannon.validate_regularization(
            fixed_scatter=True, Lambdas=Lambdas, pixel_mask=pixel_mask,
            initial_theta=None, model_filename_format="convexity-proof-3label-{}.pkl",
            overwrite=True, xtol=1e-4, ftol=1e-4)

    with open(filename, "wb") as fp:
        pickle.dump((regularizations, chi_sq, log_det, all_models), fp, -1)

else:
    with open(filename, "rb") as fp:
        regularizations, chi_sq, log_det, all_models = pickle.load(fp)


scaled_chi_sq = chi_sq - chi_sq[0]


fig, ax = plt.subplots()

colours = ("#4C72B0", "#55A868", "#C44E52", "#8172B2", "#64B5CD")

for i in range(scaled_chi_sq.shape[1]):

    ax.scatter(np.log10(Lambdas), scaled_chi_sq[:, i], facecolor=colours[i % len(colours)])
    ax.plot(np.log10(Lambdas), scaled_chi_sq[:, i], c=colours[i % len(colours)])

ax.set_xlim(np.log10(Lambdas[0]), np.log10(Lambdas[-1]))

ax.set_xlabel(r"$\log_{10}\Lambda$")
ax.set_ylabel(r"$\chi^2 + \Delta$")
ax.set_title(r"3-label $\theta_{init}={1,0...}$ + $s^2 = 0$ + Fixed_s2 + Powell + No_theta_passing + tol=1e-4")


"""

"""
# Check the effect of tolerances
wavelengths = [wavelengths[2], wavelengths[15]]
Lambdas = 10**np.hstack([[0, 1, 2], np.arange(3, 6, 0.2)])
pixel_mask = np.searchsorted(dispersion, wavelengths)

regularizations, chi_sq, log_det, all_models = \
        regularized_cannon.validate_regularization(
            fixed_scatter=True, Lambdas=Lambdas, pixel_mask=pixel_mask,
            initial_theta=None, xtol=1e-4, ftol=1e-4)

regularizations2, chi_sq2, log_det2, all_models2 = \
        regularized_cannon.validate_regularization(
            fixed_scatter=True, Lambdas=Lambdas, pixel_mask=pixel_mask,
            initial_theta=None, op_kwargs={"xtol":1e-8, "ftol":1e-8})

scaled_chi_sq = chi_sq - chi_sq[0]
scaled_chi_sq2 = chi_sq2 - chi_sq2[0]


colours = ("#4C72B0", "#55A868", "#C44E52", "#8172B2", "#64B5CD")


fig, ax = plt.subplots()
for i in range(scaled_chi_sq.shape[1]):
    ax.plot(np.log10(Lambdas), scaled_chi_sq[:, i], c=colours[i % len(colours)])


for i in range(scaled_chi_sq.shape[1]):
    ax.plot(np.log10(Lambdas), scaled_chi_sq2[:, i], c=colours[i % len(colours)], lw=2)
    
"""

#wavelengths = [wavelengths[2], wavelengths[15]]
Lambdas = 10**np.hstack([[0, 1, 2], np.arange(3, 6, 0.1)])
pixel_mask = np.searchsorted(dispersion, wavelengths)

t_init = time()
# BFGS
regularizations, chi_sq, log_det, all_models = \
        regularized_cannon.validate_regularization(
            fixed_scatter=True, Lambdas=Lambdas, pixel_mask=pixel_mask,
            initial_theta=None, 
            op_kwargs={"xtol": 1e-10, "ftol": 1e-10},
            op_bfgs_kwargs={"factr": 0.10, "pgtol": 1e-6})# "factr": 10.0, "epsilon": 1e-3})

t = time() - t_init
print(t)
# Load old stuff.
"""
import cPickle as pickle
with open("foo.pkl", "rb") as fp:
    Lambdas, chi_sq_fmin_xtol4, chi_sq_fmin_xtol8 = pickle.load(fp)
"""


def calculate_optimal_lambda(Lambda, Q, tolerance=0.1, full_output=False):
    # Return just the minimum:
    #return Lambda[np.argmin(Q)]
    #if full_output:
    #    return (Lambda[np.argmin(Q)], np.argmin(Q))

    # Return max({Lambda: Q(Lambda) < Q_min + tolerance })
    index = np.where(Q < np.min(Q) + tolerance)[0][-1]
    if full_output:
        return (Lambda[index], index)
    return Lambda[index]

colours = ("#4C72B0", "#55A868", "#C44E52", "#8172B2", "#64B5CD")

print(t)
fig, ax = plt.subplots()
"""
for i in range(chi_sq_fmin_xtol4.shape[1]):
    ax.plot(np.log10(Lambdas), chi_sq_fmin_xtol4[:, i], c=colours[i % len(colours)])

for i in range(chi_sq_fmin_xtol8.shape[1]):
    ax.plot(np.log10(Lambdas), chi_sq_fmin_xtol8[:, i], c=colours[i % len(colours)], lw=2)
"""

scaled_chi_sq_bfgs = chi_sq - chi_sq[0]

for i in range(scaled_chi_sq_bfgs.shape[1]):
    ax.plot(np.log10(Lambdas), scaled_chi_sq_bfgs[:, i], c=colours[i % len(colours)], lw=2)

    best_Lambda, index = calculate_optimal_lambda(Lambdas, scaled_chi_sq_bfgs[:,i], full_output=True)
    ax.scatter([np.log10(best_Lambda)], [scaled_chi_sq_bfgs[index,i]], facecolor=colours[i % len(colours)], s=100, zorder=100)

ax.set_xlim(0, 6)
ax.set_ylim(scaled_chi_sq_bfgs.min() - 1, 10)

raise a

raise a


# Do pixel 10 with a higher ftol:
Lambdas = 10**np.hstack([[0, 1, 2], np.arange(3, 6, 0.1)])

pixel_mask = np.searchsorted(dispersion, [wavelengths[10]])
regularizations, chi_sq, log_det, all_models = \
    regularized_cannon.validate_regularization(
        fixed_scatter=True, Lambdas=Lambdas, pixel_mask=pixel_mask,
        initial_theta=None, xtol=1e-7, ftol=1e-7)

scaled_chi_sq = chi_sq - chi_sq[0]

fig, ax = plt.subplots()
ax.scatter(np.log10(Lambdas), scaled_chi_sq, facecolor="k")
ax.plot(np.log10(Lambdas), scaled_chi_sq, c='k')
ax.set_title(dispersion[pixel_mask][0])


raise a
# Do a full training


# Plot stuff?

raise a

# Choose a single Lambda value for all pixels.


# Create a 10^5 regularization model and train it on 7/10ths the subset.
regularized_cannon.train()

regularized_cannon.save("apogee-rg-regularized-cannon.model", overwrite=True)

# Predict labels for the last 1/10th set and compare them to ASPCAP.
regularized_cannon_predicted_labels = regularized_cannon.fit(
    normalized_flux[test_set], normalized_ivar[test_set])


# Are we doing as good, or better than ASPCAP?


# How many terms did we remove? --> How has the sparsity changed?

