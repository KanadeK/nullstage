# Model and evidence boundary

NullStage deliberately uses a small, inspectable model. Its job is to rank direct-field geometry candidates before rehearsal, not to predict a room.

## Coordinates and declared data

- Position units are metres.
- `(0, 0)` is downstage-left; positive `x` is report-right and positive `y` is upstage.
- Aim is degrees counter-clockwise from positive `x`.
- Each source declares a **relative level at 1 m**. It is not asserted to be SPL.
- Each microphone declares a polar family and `off_axis_floor_db`. The floor prevents an ideal mathematical null from becoming infinite rejection.

## Distance term

For source level `L_source` and source-to-microphone distance `d` in metres:

```text
L_distance = L_source - 20 log10(d)
```

This is the point-source, free-field relationship. OSHA documents both the equation `Lp(d2) = Lp(d1) + 20 log10(d1/d2)` and its 6 dB drop per distance doubling, while warning that reflected fields are more complex: [OSHA Technical Manual, Section III, Chapter 5](https://www.osha.gov/otm/section-3-health-hazards/chapter-5).

NullStage applies the relationship at every declared distance, even though real near fields and extended sources can violate it. That limitation is emitted in every report.

## Ideal first-order polar term

The amplitude response is:

```text
R(theta) = |a + b cos(theta)|
L_polar  = max(20 log10(R), off_axis_floor_db)
```

| Pattern | `a` | `b` |
|---|---:|---:|
| omni | `1` | `0` |
| cardioid | `1/2` | `1/2` |
| supercardioid | `(sqrt(3)-1)/2` | `(3-sqrt(3))/2` |
| hypercardioid | `1/4` | `3/4` |
| figure8 | `0` | `1` |

The first-order supercardioid and hypercardioid coefficients are tabulated in the [Journal of the Acoustical Society of America](https://pubs.aip.org/asa/jasa/article/127/5/EL227/782967/Higher-order-differential-integral-microphone). Shure's live-sound guidance confirms the practical geometry behind the feature: cardioid monitors belong on the rear axis while supercardioid rejection is off-axis, and microphone choice/placement affects bleed ([official Shure guide](https://www.shure.com/damfiles/default/global/documents/publications/en/performance-production/microphone_techniques_for_live_sound_reinforcement_english.pdf-3df433145fca686a736beeb5da588efa.pdf), [cardioid versus supercardioid note](https://service.shure.com/articles/en_US/Knowledge/difference-between-cardioid-and-supercardioid)).

Manufacturer curves change with frequency and model. NullStage does not claim that these ideal families reproduce a specific microphone.

## Contributions, power sum, and margin

For each source/microphone pair:

```text
L_received = L_source - 20 log10(distance_m) + L_polar
```

The target contribution is the microphone's declared `target_source`. Every other source is spill. Independent spill levels are combined in linear power:

```text
L_spill = 10 log10(sum(10^(L_i / 10)))
margin  = L_target - L_spill
```

A positive margin means the declared target is stronger than the combined declared spill under this model. It does not mean the recording is clean or the PA is stable.

## Bounded optimizer

For each microphone independently, NullStage enumerates a position lattice and aim lattice inside:

- `move_radius_m` and `position_step_m`;
- `aim_range_deg` and `aim_step_deg`;
- `min_target_distance_m..max_target_distance_m`;
- the measured stage rectangle;
- the 50,000-candidate cap.

The baseline is always included. Candidates are ranked by:

1. higher target-to-spill margin;
2. less movement;
3. less rotation;
4. stable smaller `x`, `y`, then normalized aim.

This makes identical inputs deterministic. Microphones do not interact in v0.1; stand collisions, performer movement, cable reach, and shared placement constraints remain manual checks.

## Explicit non-goals

NullStage does not model:

- reflections, reverberation, room modes, barriers, or diffraction;
- phase, comb filtering, time alignment, or frequency bands;
- loudspeaker/instrument directivity or manufacturer microphone curves;
- absolute SPL, exposure, feedback, gain-before-feedback, or system safety;
- 3D height, stand stability, cables, sightlines, or performer motion.

Every JSON/HTML/SVG/terminal report repeats the direct-field boundary so an artifact cannot be separated from its assumptions.
