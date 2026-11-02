# Linux system information

`linuxsystem.bui` is an original Buoy 0.72.0 wrapper around Linux/glibc system-information calls. The feature area was inspired by [Monkeybread Software's Linux integrations](https://www.monkeybreadsoftware.de/xojo/plugin-linux.shtml); no plugin implementation or Xojo dependency is included.

Copy the module beside your entry file and use `Import linuxsystem As LinuxSystem`. The accompanying `system-smoke.bui` is a complete usage example. When declaring the snapshot variable, use the unqualified type name `SystemSnapshot`; Buoy 0.72.0 does not resolve `LinuxSystem.SystemSnapshot` as a class type through an import alias.

`IsSupported()` returns a `Boolean` on every target. All other APIs and the snapshot class are defined inside `#If TargetLinux`; guard their use in portable programs. The native layout supports 64-bit glibc Linux on x86-64 and ARM64.

| API | Result | Meaning |
| --- | --- | --- |
| `ReadSystemInfo()` | `SystemSnapshot` | One sample from `sysinfo`; no automatic refresh |
| `OnlineProcessorCount()` | `Integer` | System CPUs currently online, from `get_nprocs` |
| `ConfiguredProcessorCount()` | `Integer` | System CPUs configured, including offline CPUs, from `get_nprocs_conf` |

The snapshot class has these public properties:

| Properties | Type | Units |
| --- | --- | --- |
| `UptimeSeconds` | `Integer` | Kernel uptime in whole seconds |
| `LoadAverage1Minute`, `LoadAverage5Minutes`, `LoadAverage15Minutes` | `Double` | Load averages, converted from native 16-bit fixed point |
| `TotalRamBytes`, `FreeRamBytes`, `SharedRamBytes`, `BufferRamBytes` | `UInt64` | Bytes, multiplied by the native memory unit |
| `TotalSwapBytes`, `FreeSwapBytes` | `UInt64` | Bytes, multiplied by the native memory unit |
| `TotalHighRamBytes`, `FreeHighRamBytes` | `UInt64` | Bytes; high memory is usually zero on these targets |
| `ProcessCount` | `Integer` | Native unsigned 16-bit kernel process/task counter |
| `MemoryUnitBytes` | `Integer` | Native `mem_unit`, retained for diagnostics; byte properties are already scaled |

The Linux [sysinfo contract](https://man7.org/linux/man-pages/man2/sysinfo.2.html) defines the memory fields and unit scaling. `FreeRamBytes` means free RAM, which differs from the kernel's `MemAvailable` estimate. System metrics may describe the host rather than container cgroup limits. `ProcessCount` is limited by the native 16-bit field and can wrap on very large systems; it is not a count of processes visible through your PID namespace.

CPU counts follow the [glibc get_nprocs contract](https://man7.org/linux/man-pages/man3/get_nprocs.3.html). They are logical system CPU counts, and do not measure this process's affinity or container CPU quota. CPU hotplug may change results between calls. Load averages measure demand, rather than CPU utilization percentages.

All native calls use `Private Optional Declare Lib "c"`, resolving `libc.so.6` at runtime without depending on Buoy's incomplete SDK symbol stubs. A failed `sysinfo` call, zero memory unit, or invalid CPU count raises `RuntimeException`; unavailable native libraries or symbols raise `LibraryUnavailableException`. No subprocesses, GUI, or third-party packages are needed.
