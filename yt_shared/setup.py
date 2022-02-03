from setuptools import find_packages, setup


# metadata
VERSION = (0, 0, 1)
__author__ = 'tropicoo'
__email__ = 'good@example.com'
__version__ = '.'.join(map(str, VERSION))


setup_requirements = []

setup(
    name='yt_shared',
    author=__author__,
    author_email=__email__,
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    description='Common shared utils for yt downloader bot',
    install_requires=[
    ],
    include_package_data=True,
    keywords='yt-shared',
    packages=find_packages(),
    setup_requires=setup_requirements,
    version=__version__,
    zip_safe=False,
)
