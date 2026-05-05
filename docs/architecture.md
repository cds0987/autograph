auto_graph/
├── __init__.py
├── core/
│   ├── graph_builder.py      # Main class
│   ├── config.py              # Configuration
│   └── exceptions.py          # Custom errors
├── loaders/
│   ├── json_loader.py         # JSON support
│   ├── csv_loader.py          # CSV support
│   └── auto_detector.py       # Auto-detect format
├── analyzers/
│   ├── schema_analyzer.py     # Analyze data structure
│   ├── entity_extractor.py    # LLM entity extraction
│   └── relationship_builder.py # Infer relationships
├── embeddings/
│   ├── embedding_generator.py # Generate vectors
│   └── vector_index.py        # Vector search setup
├── neo4j/
│   ├── connection.py          # Neo4j driver
│   ├── schema_manager.py      # Constraints/indexes
│   └── query_builder.py       # Cypher generation
└── utils/
    ├── llm_client.py          # OpenAI/Anthropic wrapper
    └── validators.py          # Data validation