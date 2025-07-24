# NoxPanel Suite - Project Structure Consolidation Plan

## CURRENT STRUCTURE ISSUES
- AI/NoxPanel/ (2,400+ files) - Complete duplicate system
- Multiple docker-compose.yml files with conflicts
- Plugin systems in /plugins and /AI/NoxPanel/plugins
- Inconsistent module imports and paths

## RECOMMENDED CONSOLIDATION

### Primary Structure (Keep)
```
K:\Project Heimnetz\
├── src/                    # Main source code
│   ├── noxpanel/          # Core NoxPanel system
│   ├── aethercore/        # Inference server
│   ├── contextforge/      # LLM context manager
│   └── plugins/           # Plugin ecosystem
├── config/                # Unified configuration
├── docker/               # Docker configurations
│   ├── docker-compose.yml
│   ├── docker-compose.dev.yml  
│   ├── docker-compose.prod.yml
│   └── docker-compose.override.yml
├── k8s/                  # Kubernetes manifests
├── docs/                 # Documentation
├── scripts/              # Automation scripts
└── tests/                # Test suites
```

### Migration Tasks
1. Consolidate AI/NoxPanel/ → src/noxpanel/
2. Merge plugin systems
3. Standardize import paths
4. Update all docker-compose references

### Performance Benefits
- Reduced indexing from 2,740+ → ~800 files
- Cleaner IntelliSense and autocomplete
- Faster git operations
- Reduced memory footprint
