VENV_PATH = ./venv

.PHONY: all
all: run

# Run the application
.PHONY: run
run:
	@echo "Running the application..."
	@if [ ! -d $(VENV_PATH) ]; then \
		$(MAKE) install; \
	fi
	@$(VENV_PATH)/bin/python3 lambda/main.py

# Create a virtual environment and install dependencies
.PHONY: install
	
install:
	@echo "Installing dependencies..."
	@if [ ! -d $(VENV_PATH) ]; then \
		echo "Creating virtual environment..."; \
		python3.12 -m venv $(VENV_PATH); \
	fi
	@$(VENV_PATH)/bin/pip3 install -r requirements.txt

.PHONY: clean
clean:
	@echo "Cleaning up..."
	@rm -rf $(VENV_PATH)
