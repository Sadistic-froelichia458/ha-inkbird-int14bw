# Cook Control dashboard

A ready-made "Cook Control" Lovelace dashboard for the Inkbird INT-14-BW —
radial probe gauges that change colour by doneness, editable per-probe targets,
one-tap recipe presets, a °C/°F toggle, and target-reached alerts.

![Cook Control dashboard](screenshot.png)

> Open [`concept.html`](concept.html) in any browser for an interactive live
> preview of the design (temperatures are simulated).

## The two files, and why you need both

This dashboard is made of **two** files that do very different jobs:

| File | What it is | Where it goes | What it does |
|---|---|---|---|
| [`inkbird_package.yaml`](inkbird_package.yaml) | The **back-end** (the engine) | `<config>/packages/` | Creates the helpers and logic the dashboard needs: the target temperature per probe, probe names, the active-probe selector, the °C/°F toggle, the "apply recipe" script, and the **automation that sends an alert when a probe reaches its target**. You never see these directly. |
| [`inkbird_dashboard.yaml`](inkbird_dashboard.yaml) | The **front-end** (what you see) | A Lovelace dashboard | The visual dashboard itself: the probe cards, radial gauges, recipe buttons, alerts panel. |

**You need both, and the order matters:** add the package first (step 2), then the
dashboard (step 3). The dashboard reads the helpers the package creates — without
the package, the targets, recipe buttons, and °C/°F toggle have nothing to talk to.

## 1. Prerequisites

Install these from **HACS → Frontend**:

- [`button-card`](https://github.com/custom-cards/button-card)
- [`card-mod`](https://github.com/thomasloven/lovelace-card-mod)

## 2. Add the helpers & automations

Copy [`inkbird_package.yaml`](inkbird_package.yaml) into your
`<config>/packages/` folder and make sure packages are enabled in
`configuration.yaml`:

```yaml
homeassistant:
  packages: !include_dir_named packages
```

This creates:

- `input_number.inkbird_target_1…4` — the target temperature per probe
- `input_text.inkbird_name_1…4` — the probe/cook name (set by recipes)
- `input_select.inkbird_active_probe` — which probe a recipe applies to
- `input_select.inkbird_unit` — the dashboard °C/°F toggle
- `sensor.inkbird_probe_1…4_state` — cook state (idle/heating/close/ready)
- `script.inkbird_apply_recipe` — applies a recipe to the active probe
- an automation that posts a notification when any probe reaches its target

Restart Home Assistant after adding it.

## 3. Add the dashboard

Create a new dashboard (⋮ → **Edit dashboard** → ⋮ → **Raw configuration
editor**) and paste [`inkbird_dashboard.yaml`](inkbird_dashboard.yaml), or copy
the `views:` block into an existing dashboard.

## 4. Match your entity IDs

The package and dashboard assume the probe sensors are named:

```
sensor.int_14_bw_probe_1 … _4
sensor.int_14_bw_battery
```

If your entity IDs differ (check **Settings → Devices & Services → Entities**),
update them in both `inkbird_package.yaml` and `inkbird_dashboard.yaml`.

## Notes

- **Recipes** apply to whichever probe is selected in **Active probe**. Pick the
  probe first, then tap a recipe.
- The dashboard's °C/°F toggle is **display only** — targets are stored in °C.
  For the gauge maths to line up, keep the integration's temperature-unit
  option on **Follow Home Assistant** (with a metric system) or **Celsius**.
- **Phone push:** edit the automation in `inkbird_package.yaml` and uncomment
  the `notify.mobile_app_…` block with your own notify service.
