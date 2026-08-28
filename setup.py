from setuptools import find_packages, setup

setup(
    name="memtest",
    version="0.1.0",
    description="Cognitive load assessment game and tools (vendored)",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[],  # Add any specific dependencies if needed
    author="TSSlade",
    license="MIT",
)
