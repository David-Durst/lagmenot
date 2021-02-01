from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='lagmenot',
    version='0.0.1',
    url='https://github.com/David-Durst/lagmenot',
    license='MIT',
    maintainer='David Durst',
    maintainer_email='davidbdurst@gmail.com',
    description='Test-bed for client-side prediction vs lag compensation vs rollback.',
    packages=[
        "lagmenot",
    ],
    install_requires=[
        'pygame',
    ],
    python_requires='>=3.8',
    long_description=long_description,
    long_description_content_type="text/markdown"
)
