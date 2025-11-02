import setup_model

try:
    setup_model.main()
except Exception as e:
    print(f"⚠️  An error occurred while setting up the model: {e}")