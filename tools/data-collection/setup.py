from setuptools import setup, find_packages

setup(
    name="zerocompress-data-tools",
    version="0.1.0",
    description="Data collection and analysis tools for the ZeroCompress project",
    author="ZeroCompress Team",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'web3>=5.30.0',
        'pandas>=1.3.0',
        'numpy>=1.20.0',
        'matplotlib>=3.4.0',
        'requests>=2.25.0',
        'tqdm>=4.60.0',
        'eth-utils>=2.0.0',
    ],
    entry_points={
        'console_scripts': [
            'zc-collect=scripts.transaction_collector:main',
            'zc-analyze-run=scripts.run_analysis:main',
        ],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    python_requires='>=3.7',
) 