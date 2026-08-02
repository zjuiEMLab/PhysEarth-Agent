# Comparing two physical models honestly

Before you compare two model runs, establish that they are comparable. Work through the
matrix below and state in the answer which rows you could align and which you could not.

| Row | What to check |
| --- | --- |
| Observable | Both runs must produce the same quantity. Brightness temperature and backscatter are different observables and cannot be differenced. |
| Frequency and angle | Same sensor configuration, or the difference in configuration is the thing being studied and is stated as such. |
| Medium | Same medium. A snowpack model and a soil-vegetation model do not describe the same surface. |
| Parameter meaning | The same name can mean different things. Check the unit and the description in each declaration before treating two parameters as the same quantity. |
| Held-fixed values | Everything not being varied must match, including the defaults you did not set. Defaults differ between models. |
| Validity | Both runs must sit inside the range each model declares. A run at the edge of a declared range is a weaker basis for a claim. |

If any row cannot be aligned, you may still report both results, but you must say that the
difference includes the effect of that misalignment and is not attributable to the physics
alone.

Two failure modes to avoid.

Attributing a difference to a formulation when the configurations differ. If model A ran at
19 GHz and model B at 37 GHz, the difference is dominated by frequency, not by the choice of
formulation.

Comparing a quantity with its own transform. Emissivity and brightness temperature are not
independent evidence; reporting both as if they were two agreeing results overstates the
support.

When the models genuinely are comparable, report the two values, the difference, and the
configuration they share. When they are not, say so first and report the values second.
