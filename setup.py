import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name='nd2handling',
    version='0.0.1',
    author='Oskar E. Strom',
    author_email='oskarestrom@protonmail.com',
    description='ND2 File Handling',
    # long_description=long_description,
    # long_description_content_type="text/markdown",
    # url='',
    # project_urls = {
    #     "Bug Tracker": ""
    # },
    license='Oskar E. Strom',
    packages=['nd2handling'],
    install_requires=[
            'pims',
            'nd2reader',
            'pandas',
            'numpy',
            ],
)