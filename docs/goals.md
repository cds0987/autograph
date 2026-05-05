# Auto Graph Builder Framework

> **Transform any dataset into a Knowledge Graph with just a few lines of code**

---

## 🎯 Vision

A framework that automatically converts structured data (JSON, CSV, Excel) into optimized Neo4j graph databases using LLM-powered entity extraction and optional embeddings.

**Goal:** Enable developers to build knowledge graphs without graph expertise.

---

## 💡 The Problem

Building a graph database today requires:

```python
# Current approach: 100+ lines of code + expertise

1. Manually design graph schema
   - Which nodes? Which relationships?
   - What properties to store?
   
2. Write entity extraction logic
   - Parse text fields
   - Extract organizations, people, locations
   - Handle edge cases
   
3. Create database schema
   - Write Cypher for constraints
   - Create indexes for performance
   - Test and debug
   
4. Insert data
   - Write complex Cypher queries
   - Handle batching
   - Error handling
   
5. Add embeddings (optional)
   - Generate vectors
   - Create vector indexes
   - Sync with graph

6. Optimize & maintain
   - Monitor performance
   - Add new indexes
   - Update schema
```

**Result:** Takes days/weeks, requires Neo4j expertise, error-prone.

---

## ✨ Our Solution

```python
# Auto Graph approach: 3 lines

from autograph import GraphBuilder

builder = GraphBuilder(
    llm_api_key="sk-...",           # OpenAI or Anthropic
    neo4j_uri="bolt://localhost:7687",
    neo4j_password="password",
    use_embeddings=True              # Optional
)

builder.load_data("data.json").build_graph()
```

**Result:** Working knowledge graph in minutes, zero graph expertise needed.

### What Happens Automatically

```
1. 🤖 LLM analyzes your data structure
   → Designs optimal graph schema
   → Suggests node types & relationships

2. 🧠 LLM extracts entities from text
   → Organizations, people, locations, etc.
   → Creates connections automatically

3. ⚡ Framework optimizes database
   → Creates constraints for uniqueness
   → Adds indexes for performance
   → Batch processing for efficiency

4. 📊 Optional: Generates embeddings
   → Vector representations of text
   → Enables semantic search
   → Hybrid graph + vector queries
```

---

## 🌟 Core Capabilities

### 1. **Zero Configuration**
- No manual schema design
- No Cypher knowledge required
- Works out of the box

### 2. **LLM-Powered Intelligence**
- Automatic schema detection
- Smart entity extraction
- Relationship inference

### 3. **Multi-Format Support**
- JSON files
- CSV spreadsheets  
- Excel workbooks
- Pandas DataFrames

### 4. **Optional Semantic Search**
- Toggle embeddings on/off
- Automatic vector indexing
- Hybrid graph + semantic queries

### 5. **Production Ready**
- Auto-optimization
- Batch processing
- Error handling
- Performance monitoring

---

## 🏗️ How It Works

```
┌──────────────────────────────────────────────────────┐
│              YOUR DATA (JSON/CSV/Excel)              │
└────────────────────┬─────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────┐
│                 AUTO GRAPH BUILDER                   │
│                                                      │
│  Step 1: Analyze Data                               │
│  ├─ LLM examines structure                          │
│  └─ Designs graph schema                            │
│                                                      │
│  Step 2: Extract Entities                           │
│  ├─ LLM reads text fields                           │
│  └─ Identifies entities & relationships             │
│                                                      │
│  Step 3: Build Graph                                │
│  ├─ Create nodes & relationships                    │
│  ├─ Add constraints & indexes                       │
│  └─ Optimize for queries                            │
│                                                      │
│  Step 4: Optional Embeddings                        │
│  ├─ Generate vectors                                │
│  └─ Create vector index                             │
└────────────────────┬─────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────┐
│           NEO4J KNOWLEDGE GRAPH (Ready!)             │
└──────────────────────────────────────────────────────┘
```

### Key Components

1. **Data Loaders** - Understand your data format
2. **Schema Analyzer** - LLM designs graph structure  
3. **Entity Extractor** - LLM finds entities in text
4. **Graph Manager** - Builds optimized Neo4j database
5. **Embedding Generator** - Optional semantic search

---

## 🚀 Quick Start

### **Basic Usage**

```python
from autograph import GraphBuilder

# Initialize
builder = GraphBuilder(
    llm_api_key="sk-...",
    neo4j_uri="bolt://localhost:7687",
    neo4j_password="password"
)

# Build graph automatically
builder.load_data("data.json").build_graph()

# Search
results = builder.search("AI regulation")
```

### **With Semantic Search**

```python
builder = GraphBuilder(
    llm_api_key="sk-...",
    neo4j_uri="bolt://localhost:7687",
    neo4j_password="password",
    use_embeddings=True  # Enable vector search
)

builder.load_data("data.json").build_graph()

# Semantic search automatically enabled
results = builder.search("government AI policy")
```

### **Different Data Formats**

```python
# JSON
builder.load_data("news.json")

# CSV
builder.load_data("products.csv")

# Excel
builder.load_data("customers.xlsx")

# All trigger automatic processing
builder.build_graph()
```

---

## 🎨 Example Use Cases

### **News & Media**
Transform RSS feeds and articles into searchable knowledge graphs with automatic entity extraction and topic clustering.

### **E-Commerce**
Build product catalogs with automatic category hierarchies, brand relationships, and customer review connections.

### **Research & Academia**  
Create citation networks from paper databases with author affiliations and topic relationships.

### **Social Networks**
Map user interactions, followers, and content sharing patterns automatically from platform exports.

### **Business Intelligence**
Convert CRM data into relationship graphs showing customer journeys, sales patterns, and market segments.

---

## ⚙️ Configuration

### **Minimal Setup**
```python
builder = GraphBuilder(
    llm_api_key="sk-...",
    neo4j_uri="bolt://localhost:7687",
    neo4j_password="password"
)
```

### **Common Options**
```python
builder = GraphBuilder(
    # Required
    llm_api_key="sk-...",
    neo4j_uri="bolt://localhost:7687",
    neo4j_password="password",
    
    # Optional
    use_embeddings=True,        # Enable semantic search
    llm_provider="openai",      # or "anthropic"
    verbose=True                # Show progress
)
```

---

## 🤖 How LLM Powers the Framework

### **Automatic Schema Detection**

The framework sends sample data to LLM:

**Input:** Sample of your data
```json
[
  {
    "title": "White House considers AI regulation",
    "source": "NYT",
    "content": "The White House is discussing..."
  }
]
```

**LLM Analyzes and Returns:**
```json
{
  "node_types": [
    {"label": "Article", "id_field": "url"},
    {"label": "Source", "id_field": "name"},
    {"label": "Entity", "id_field": "name"}
  ],
  "relationships": [
    {"type": "PUBLISHED_BY", "from": "Article", "to": "Source"},
    {"type": "MENTIONS", "from": "Article", "to": "Entity"}
  ]
}
```

**Framework creates the graph automatically based on this schema.**

---

### **Automatic Entity Extraction**

For each record, LLM extracts entities:

**Input Text:**
```
"White House considers vetting AI models. 
The Biden administration is exploring..."
```

**LLM Extracts:**
```json
{
  "organizations": ["White House", "Biden administration"],
  "technologies": ["AI models"],
  "people": []
}
```

**Framework creates nodes and relationships for these entities.**

---

## ⚡ Performance & Costs

### **Processing Time Estimates**

| Dataset Size | Processing Time | With Embeddings |
|--------------|----------------|-----------------|
| 100 records | ~2 minutes | ~5 minutes |
| 1,000 records | ~15 minutes | ~40 minutes |
| 10,000 records | ~2 hours | ~6 hours |

*Using GPT-4 and standard embedding models*

### **Cost Estimates (OpenAI)**

**For 1,000 records:**
- Schema analysis: ~$0.01
- Entity extraction: ~$2.00
- Embeddings (optional): ~$0.02
- **Total: ~$2.03**

### **Neo4j Requirements**

- **Free tier**: 200MB (suitable for ~10-50k articles)
- **Production**: Aura Pro $65/month (8GB+)

---

## 🎯 Target Users

**Primary:**
- Data Scientists who know Python but not Neo4j
- Backend Developers building features quickly
- ML Engineers needing knowledge graphs for RAG

**Secondary:**
- Researchers creating quick prototypes
- Startups building MVPs fast
- Students learning about graphs

---

## 💎 Value Proposition

### **For Developers**
- ✅ 90% less code required
- ✅ Zero graph expertise needed
- ✅ Production-ready in minutes

### **For Businesses**
- ✅ Faster time to market
- ✅ Lower development costs
- ✅ Easier maintenance

### **For Projects**
- ✅ Rapid prototyping
- ✅ Easy experimentation
- ✅ Scalable foundation

---

## 🚀 Getting Started

```bash
# Install (when available)
pip install auto-graph

# Use
from autograph import GraphBuilder

builder = GraphBuilder(
    llm_api_key="sk-...",
    neo4j_uri="bolt://localhost:7687",
    neo4j_password="password"
)

builder.load_data("your_data.json").build_graph()
```

---

## 📝 Summary

**Auto Graph Builder** transforms any dataset into a knowledge graph with minimal code. 

- **Zero configuration** - LLM handles schema design
- **Smart extraction** - Entities detected automatically  
- **Production ready** - Optimized and scalable
- **Developer friendly** - Works like familiar Python libraries

**Built for developers who want graphs, not graph expertise.**
