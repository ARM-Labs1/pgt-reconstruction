# Prompt Gamma Timing Simulation for Bragg Peak Localisation in Proton Therapy

## Theory

Proton therapy is a form of charged particle therapy that uses a beam of protons in order to irradiate tissue. The advantage of proton therapy over other forms of radiotherapy is that the majority of the dose is deposited within a narrow range of depth. The location of dose deposition depends on the energy of the proton beam and is characterised by the Bragg peak shown below.

<img width="1280" height="886" alt="image" src="https://github.com/user-attachments/assets/096ff7cb-e52f-4fb6-af49-21efa873aabf" />

Notice the small range of depth where the dose has been deposited at around 23 cm for the native proton beam. Compare the dose distribution between the X-ray beam and the proton beam.

Proton therapy is particularly useful when treating cancers in sensitive locations, where it is imperative that the damage to surrounding tissue is minimised. Some cancer types where proton therapy yields better results compared to other forms of radiotherapy include head and neck cancers, as well as selected pelvic tumours.

However, there is a challenge with proton therapy involving dose verification. Due to the sensitive areas where cancers are being treated, it is important to ensure that the dose is deposited in the correct location. One method for dose verification involves the prompt gamma (PG) rays emitted by nuclear interactions as the protons traverse the tissue. The emission rate of these gamma rays is correlated with the dose deposition profile. By placing a detector laterally to the proton path, one can measure the time at which a PG ray arrives at the detector and infer where the gamma photon was emitted by combining the proton and gamma time-of-flight. This method enables non-invasive verification of the Bragg peak position during treatment.

## Method

The simulation consisted of both a forward model, simulating the PG emission, and a reconstruction algorithm.

### Forward Model

A one-dimensional water phantom of length 300 mm was used, with a detector of area 25 cm² placed 50 mm laterally from the beam axis and 50 mm beyond the end of the phantom. The Bragg peak was set at a depth of 150 mm, corresponding to an initial proton energy of approximately 145.7 MeV.

Proton velocities at each depth were calculated using relativistic kinematics:

$$\beta = \sqrt{1 - \left(\frac{m_p c^2}{E + m_p c^2}\right)^2}$$

where $m_p c^2 = 938.3$ MeV is the proton rest mass energy and $E$ is the kinetic energy at that depth. The energy at each depth was determined from tabulated range-energy data obtained from the NIST PSTAR database by linear interpolation. The proton time-of-flight to each depth was then computed by numerical integration of $1/v(z)$ along the path using the trapezoidal rule.

The Bragg curve was modelled as a constant entrance dose combined with a Gaussian peak and an exponential fall-off beyond the peak position, as seen below.
<img width="850" height="458" alt="tdd" src="https://github.com/user-attachments/assets/03decd53-f706-4ecf-ae34-23510fd3a2bc" />


The number of gamma photons emitted at each depth was taken to be proportional to the local dose, scaled by the yield (10⁻⁴ photons per proton) and the number of protons per burst (5 × 10¹¹).

The number of photons reaching the detector from each depth was calculated by accounting for:
- Solid angle subtended by the detector: $\Omega = A / (4\pi d^2)$
- Attenuation in tissue: $\exp(-\mu d)$ with $\mu = 0.06$ cm⁻¹
- Poisson statistics for photon counting
- Background radiation (modelled as Poisson-distributed noise)
- Timing jitter from detector resolution (modelled as Gaussian with $\sigma = 0.5$ ns)

The total measured time for each detected photon was calculated as the sum of the proton time-of-flight to the emission point and the gamma time-of-flight from that point to the detector.

### Reconstruction Algorithm

The reconstruction employed a temporal back-projection algorithm. Measured arrival times were binned into a histogram with bin width 0.05 ns. For each time bin, the expected arrival time from every possible emission depth was calculated as:

$$t_{\text{expected}}(z) = t_{\text{proton}}(z) + t_{\gamma}(z)$$

where $t_{\text{proton}}(z)$ is the proton time-of-flight to depth $z$ and $t_{\gamma}(z)$ is the gamma time-of-flight from depth $z$ to the detector.

A Gaussian weighting function assigned probability to each depth based on how closely its expected time matched the measured time:

$$w(z) = \exp\left(-\frac{(t_{\text{measured}} - t_{\text{expected}}(z))^2}{2\sigma^2}\right)$$

where $\sigma$ is the detector timing resolution. This weighting represents the characteristic smearing inherent to back-projection methods. The contributions from all time bins were summed, and a sensitivity correction was applied to account for geometric $1/r^2$ detection bias and gamma attenuation.

## Results

The reconstructed dose profile was compared against the theoretical Bragg curve. The reconstruction successfully identified the Bragg peak position, demonstrating the feasibility of prompt gamma timing for range verification. However, there was significant noise around the location of the Bragg peak. Despite the noise, however, the peak of the reconstructed curve still matched the theoretical curve.
<img width="915" height="480" alt="Figure_1" src="https://github.com/user-attachments/assets/882039b2-a694-4c98-826e-40d15cede73b" />
<img width="915" height="480" alt="Figure_2" src="https://github.com/user-attachments/assets/93d78555-f145-4821-8d59-7dd0f489fee5" />

The increased noise in the region before the peak arises from a fundamental property of the time-to-position mapping. As protons approach the Bragg peak, they lose energy rapidly and slow down dramatically. The proton time-of-flight is given by:

$$t_p(z) = \int_0^z \frac{dz'}{v(z')}$$

Near the peak where $v(z) \to 0$, the derivative $dt/dz \to \infty$. This means that a fixed timing uncertainty (0.5 ns detector resolution) translates to a much larger spatial uncertainty near the Bragg peak than at the phantom entrance. At the entrance, where the proton travels at approximately 0.5c, timing jitter smears photon origins over a relatively large but sparsely-emitting region. Near the peak, where the proton velocity drops rapidly near the Bragg peak so a fixed timing uncertainty translates to a much larger spatial uncertainty close to the stopping point, degrading spatial resolution precisely where the dose gradient is steepest. This depth-dependent spatial resolution is a fundamental limitation of prompt gamma timing methods.


## Conclusion

A computational simulation of prompt gamma timing for Bragg peak localisation in proton therapy was developed and tested. The simulation incorporated a physically motivated forward model including relativistic proton kinematics, gamma attenuation, solid angle effects, and detector timing jitter. A temporal back-projection algorithm was implemented to reconstruct the dose profile from simulated detector measurements. The results demonstrate that prompt gamma timing can successfully localise the Bragg peak under realistic conditions. However, the results exhibit degraded spatial resolution near the Bragg peak due to the nonlinear time-to-position mapping as protons decelerate, a fundamental limitation of timing-based methods

If this project were to be extended, several improvements could be made, such as an extension to two- or three-dimensional geometry with realistic anatomical phantoms, inclusion of tissue heterogeneity (bone, lung, soft tissue) rather than a uniform water phantom, and the implementation of filtered back-projection in order to reduce the noise in the reconstructed data.
