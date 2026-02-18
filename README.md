# Secure Census Data Platform

## Overview

A secure web-based data ingestion platform for collecting, cleaning, standardizing, and distributing census-style datasets.

The system provides trade unions with a simple upload interface while automatically transforming raw files into a validated, consistent "source of truth" dataset. Internal administrators can review, download, and manage data as well as manage authorized personnel through an audited dashboard designed for non-technical users.

This project was built as a production tool for handling sensitive data with strong security, auditability, and operational reliability. Several importable packages and libraries were created with the app in mind to ensure modularity. (See below for the repository links to these packages/libraries.)

## Architecture

High-level flow:

Upload --> Validation --> Cleaning and Standardization --> Database Storage --> Secure Distribution

Components:

- Flask web application
- OAuth authentication (Google + Microsoft)
- File ingestion & processing pipeline
- MariaDB storage
- Role-based access control
- Audit logging
- Optional SFTP ingestion

## Key Features

#### Secure Authentication
- Google and Microsoft OAuth
- Role-based access control
- Session management with Flask-Login

#### File Ingestion
- Drag-and-drop uploads (CSV, Excel, TXT)
- Optional SFTP ingestion
- Automatic validation and cleaning

#### Data Standardization
- Column mapping and normalization
- Deduplication
- Standardized output format

#### Admin Dashboard
- Browse and download processed files
- Manage users and permissions
- Audit logs for all admin actions

#### Auditability
- All uploads and admin actions logged
- Traceable file history

## Internal modules used:
- flask-dbmanager
- flask-dragdrop
- census_cleaning