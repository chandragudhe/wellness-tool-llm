# Version 3 Classic UI Merge

## Preserved from earlier UI
- Multi-step WellnessFlow interface
- Existing form fields and auto-filled review values
- BMI, BP, SpO2, pulse and temperature calculations
- Manual lifestyle path
- Final vital snapshot
- Existing result cards and summary layout
- Camera capture and upload controls

## Replaced with Version 3 capability
- Local face-validation gate removed from the AI path
- Photo is sent to the secure `/api/wellness-analysis` backend only when the user starts AI analysis
- Image and current vital values are analyzed together by the configured OpenRouter route
- AI response is shown in Step 3 and incorporated into the final vital snapshot
- New **Test AI connection** button uses `/api/llm-status`
- Detailed provider errors are shown instead of the old Invalid Face block
