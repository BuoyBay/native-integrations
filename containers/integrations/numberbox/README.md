# View-based native NumberBox

A reusable View-based validated numeric editor, built entirely from
managed native `TextField` and `Stepper` controls. No Canvas drawing,
HTML, polling, platform widget replacement, or extra native library is involved.

- macOS uses `NSTextField` and `NSStepper`.
- Windows uses native `EDIT` and Up-Down controls.
- Linux uses `GtkEntry` and Buoy's two-native-button Stepper composition.

The standard text field retains the platform's editing, selection, clipboard,
and input-method behavior. The stepper serves as a direction control; NumberBox
owns the numeric value. This avoids Windows Up-Down's quantization of arbitrary
fractional value ranges.

Copy [numberbox.bui](numberbox.bui) into your project and `Import numberbox`.
[example.bui](example.bui) is a complete runnable window with invariant and
comma-decimal entries and an explicit Commit button.

## API and behavior

| Member | Contract |
| --- | --- |
| `Value As Double` | Finite value clamped to the current bounds. Default 0. Direct assignment is silent. |
| `Minimum`, `Maximum` | Finite bounds, default 0 and 100. Inverted bounds throw; assignments silently clamp Value. Set Maximum first when moving the entire range above its current maximum, and Minimum first when moving it below its current minimum. |
| `Increment` | Positive finite amount per step, default 1. |
| `DecimalPlaces` | Display precision, 0–12, default 2. This is formatting only; unedited commits retain the full Double value. |
| `DecimalSeparator` | One nonnumeric character, default `.`. Set explicitly from `Locale.Current().DecimalSeparator` for localized decimal entry. |
| `EditText` | Current draft. Setting stages text without changing Value or raising events. |
| `HasPendingEdit` | Whether a native edit or EditText assignment awaits validation. |
| `Commit() As Boolean` | Validate the draft, clamp to bounds and notify if Value changes. Returns False for invalid or suppressed commits. |
| `StepBy(count)` | Commit any draft, then apply `count * Increment`, clamped to bounds. Invalid drafts prevent the step. Overflow clamps in the direction of the step. |
| `Revert()` | Restore the formatted committed value without raising events. |
| `IsReadOnly` | Make text read-only and disable the native stepper. |
| `InputControl As TextField` | Native field for styling, accessible labels and explicit focus. Use EditText rather than assigning InputControl.Text. |
| `ValueChanged(newValue)` | After an accepted edit or step changes Value. Value is updated before the event. |
| `ValidationFailed(rejectedText)` | Invalid draft was rejected and replaced with the previous formatted value. |
| `LastNativeError` | Last application-handler exception caught at a native event boundary. |

Edits commit when the native field loses focus, or when the application calls
`Commit()`. This version does not intercept Return or Escape; applications can
wire a window-level commit/revert action without replacing native text input.

The parser accepts signed decimal and scientific notation, surrounding
whitespace, and ASCII digits. It rejects empty/incomplete input, grouping,
currency symbols, trailing junk, NaN, and infinity. Decimal notation follows
`DecimalSeparator`; it never silently interprets a second decimal convention.
The default is explicitly invariant rather than depending on process locale.
For example, comma mode accepts `3,75` and rejects `3.75` and `1,234,5`.
Non-ASCII digit shaping and grouping-aware currency entry are outside this
control's initial contract.

Native edits may contain intermediate or invalid text while typing; validation
happens on commit. No key-level numeric filter interferes with native input
methods. Changing Value, a bound, or formatting replaces the draft silently.
Disabled, hidden, closed, and read-only controls ignore commit/step actions.
A step at an existing bound raises no ValueChanged event.

## Lifecycle and layout

The composite creates and adds its native children in its constructor, before
its host View is attached to a window. `Open()` reconnects the weak event owners,
clears LastNativeError and lays out the children. Call it in window Opening.
`Close()` detaches event owners and is idempotent; the destructor also closes.
The Buoy View owns and releases its child controls through the normal runtime.

Call `RefreshNative()` after changing the NumberBox frame or applying layout
constraints. A practical minimum frame is 100 × 32 points; native theme minimum
sizes still apply. Give `InputControl.AccessibleLabel` an application-specific
name. The field and stepper retain their individual native accessibility
objects; a single custom numeric accessibility provider has not been added.
