# ABGrid - Peer Group Analysis Software

A comprehensive open-source software for sociometric analysis and Social Network Analysis (SNA) designed to optimize peer group dynamics.

[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Mypy](https://img.shields.io/badge/type--checked-mypy-blue?style=flat-square&logo=python)](https://github.com/python/mypy)

## 🎯 Overview

ABGrid is developed for those who need to analyze group dynamics within peer groups (teams operating at the same hierarchical level). The software applies sociometric techniques and Social Network Analysis to identify key members, map relationships, and optimize group cohesion.

## 🚀 Key Features

### Core Functionality
- **Social Network Visualization**: Generate network graphs showing preference and rejection patterns
- **Key Node Identification**: Identify influential members and potential sources of instability
- **Cluster Analysis**: Map significant subgroups and relationship patterns
- **Comprehensive Reporting**: Generate detailed PDF reports with both SNA and sociometric analysis

### Analysis Capabilities
- **Sociometric Analysis**: Traditional sociometric variables including impact, balance, affiliation, and influence indices
- **SNA Metrics**: Multiple centrality measures (degree, betweenness, closeness, PageRank, Katz, Hub)
- **Network Properties**: Density, centralization, transitivity, reciprocity analysis
- **Comparative Analysis**: Side-by-side comparison of preference vs. rejection networks

## 🏗️ Architecture

The software follows a modular architecture with three main components:

### Core Module (Python)
- **NetworkX**: Graph analysis and network calculations
- **Pandas**: Data manipulation and processing
- **Matplotlib**: Graph visualization
- **Jinja2**: Report template engine
- **Pydantic**: Data validation
- **PyYAML**: Configuration management

### Server Module (Python)
- **FastAPI**: REST API framework
- **Uvicorn**: ASGI server for development
- **Gunicorn**: Production WSGI server

### User Interface Module (JavaScript)
- **Electron.js**: Cross-platform desktop application
- **Tailwind CSS**: Modern styling framework
- **Alpine.js**: Lightweight reactive framework
- **Taxi.js**: Page transitions
- **YAML.js**: Configuration file handling
- **Vite**: Build tool and development server

## 📊 Use Cases

### Applications
1. **Group Health Monitoring**: Track relationship quality using objective metrics
2. **Conflict Prevention**: Early identification of interpersonal tensions
3. **Cohesion Enhancement**: Targeted interventions based on analysis
4. **Leadership Development**: Identify informal leaders and influence patterns

## 🔬 Methodology

### Data Collection
- **Group Size**: 8-50 members
- **Sociometric Questions**: Customizable preference/rejection queries
- **Anonymous Processing**: Privacy-protected data handling

### Analysis Framework
- **Macro Level**: Network-wide properties (density, centralization, transitivity)
- **Micro Level**: Individual metrics (centrality measures, sociometric status)
- **Subgroup Level**: Cliques and strongly/weakly connected components

## 📈 Report Structure

Generated reports include:
1. **Key Nodes Summary**: List of influential and problematic members
2. **Preference Network**: Visualization and metrics for positive relationships
3. **Rejection Network**: Analysis of negative relationship patterns
4. **Comparative Analysis**: Side-by-side network comparison
5. **Sociometric Data**: Traditional sociometric variables and visualizations

## 📖 Usage

1. **Define Group**: Set up group members (8-50 individuals)
2. **Configure Questions**: Customize sociometric questions for your context
3. **Collect Data**: Gather preference/rejection responses from group members
4. **Generate Analysis**: Run automated SNA and sociometric calculations
5. **Review Reports**: Examine comprehensive PDF reports with visualizations
6. **Implement Interventions**: Use insights for targeted group optimization


## 👥 Authors

- **Dr P. Calanna, PhD** - Institute of Aerospace Medicine, Milan
- **Dr G. Buonaiuto** - Giulio Douhet Military School, Florence

## 📝 License

This project is open-source. Please refer to the license file for details.

## 🔗 Repository

[GitHub Repository](https://github.com/alkaest2002/abgrid)

## 📧 Contact

- p.calanna@gmail.com
- gaetano.buonaiuto@gmail.com

---