# Contributing to ZeroCompress

Thank you for your interest in contributing to ZeroCompress! This document provides guidelines and instructions for contributing to this project.

## Setting Up Development Environment

1. Clone the repository:
   ```
   git clone https://github.com/your-username/ZeroCompress.git
   cd ZeroCompress
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Working with Data Files

This project uses both sample data files (included in the repository) and larger test datasets (not included in the repository).

### Sample Data
- Small sample files are included in the repository under `data/sample_*.json`
- These files are sufficient for basic testing and exploration

### Large Test Datasets
- Larger test datasets are not included in the repository due to their size
- You can generate these datasets using the tools in `tools/data-collection/`
- If you need specific datasets for testing, please contact the project maintainers

## Running Benchmarks

Benchmarks can be run using the benchmark runner:

```
python -m tools.benchmarking.benchmark_runner
```

Benchmark results will be stored in `tools/benchmarking/results/` but should not be committed to the repository.

## Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature-name`)
3. Make your changes
4. Add tests for your changes
5. Run the tests to ensure they pass
6. Commit your changes (`git commit -am 'Add some feature'`)
7. Push to your branch (`git push origin feature/your-feature-name`)
8. Create a new Pull Request

## Code Style

This project follows PEP 8 style guidelines for Python code.

## License

By contributing to this project, you agree that your contributions will be licensed under the project's license. 