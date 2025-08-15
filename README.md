# SOLID Home Assistant Integration

## Dev Container mount

```
"mounts": [
  "source=${localEnv:HOME}${localEnv:USERPROFILE}/something,target=/workspaces/core/config/custom_components/solid,type=bind,consistency=cached"
]
```
