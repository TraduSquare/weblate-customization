#!/usr/bin/env python
#
# Copyright © 2020 TraduSquare
#
# Customization package information.
#
"""Setup script for TraduSquare customization package."""

from setuptools import setup

setup(
    name="tradusquare_customization",
    version="0.1",
    packages=["tradusquare_customization"],
    include_package_data=True,
    license="MIT",
    description="TraduSquare customization for Weblate",
    long_description="TraduSquare customization for Weblate",
    keywords="tradusquare i18n l10n gettext git mercurial translate",
    url="https://tradusquare.es/",
    author="TraduSquare",
    author_email="tradusquare@gmail.com",
    install_requires=["Weblate"],
    zip_safe=False,
    classifiers=[
        "Environment :: Web Environment",
        "Framework :: Django",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
        "Development Status :: 5 - Production/Stable",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Topic :: Software Development :: Internationalization",
        "Topic :: Software Development :: Localization",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
    ],
)
