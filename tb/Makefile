.PHONY: all clean $(TEST_DIRS)


# Top-level Makefile for running all Cocotb tests

# List all test directories here
TEST_DIRS = \
	proc_base \
	alu \
	ram \
	control_unit 


# Default target to run all tests
all: $(TEST_DIRS)

# Run tests in each subdirectory
$(TEST_DIRS):
	@echo "Running tests in $@..."
	@$(MAKE) -C $@

# Clean all test directories
# clean:
# 	@for dir in $(TEST_DIRS); do \
# 		echo "Cleaning $$dir..."; \
# 		$(MAKE) -C $$dir clean; \
# 	done

clean:
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type d -name "sim_build" -exec rm -rf {} +
	@find . -type f -name "results.xml" -exec rm -f {} +
	@find . -type f -name "*.None" -exec rm -f {} +
	@find . -type d -name ".pytest_cache" -exec rm -rf {} +
	@find . -type d -name ".mypy_cache" -exec rm -rf {} +
	@find . -type f -name "dump.vcd" -exec rm -f {} +

# Run individual test directory
# for to run test in alu dir run: make alu_test or for ram run: make ram_test
%_test:
	@dir=$(@:%_test=%); \
	if [ -d "$$dir" ]; then \
		echo "Running tests in $$dir..."; \
		$(MAKE) -C $$dir; \
	else \
		echo "Error: Directory $$dir does not exist"; \
		exit 1; \
	fi

# Show help
help:
	@echo "Available targets:"
	@echo "  all       - Run tests in all directories"
	@echo "  clean     - Clean all test directories"
	@echo "  <dir>     - Run tests in the specified directory"
	@echo "  <dir>_test - Alternative way to run tests in a directory"
	@echo ""
	@echo "Test directories:"
	@for dir in $(TEST_DIRS); do \
		echo "  $$dir"; \
	done
