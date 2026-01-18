# TODO: Fix Ingredient Details in PDF Generation

## Current Issue
- Ingredients are fetched dynamically from database in dictionary format
- PDF generation function expects string format like "Rice - 5 kg"
- This mismatch causes ingredient details to not display correctly in PDFs

## Tasks
- [ ] Update `generate_grocery_pdf` function in `backend/utils/pdf_routes.py` to handle dictionary-formatted ingredients
- [ ] Add logic to convert dictionary ingredients to string format for display
- [ ] Ensure backward compatibility with existing string format
- [ ] Test PDF generation with dictionary-formatted ingredients

## Files to Edit
- `backend/utils/pdf_routes.py` (only the ingredients processing logic)

## Notes
- Do not touch other PDF details, only fix ingredient fetching
- Maintain existing PDF layout and other sections
