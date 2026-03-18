# 🤖 Agentic Search Upgrade

## Overview

The system has been upgraded from **non-reasoning web search** to **agentic search with reasoning models** for more intelligent and comprehensive event discovery.

---

## 🔄 What Changed?

### **Before: Non-Reasoning Web Search**
- Used `gpt-4o` (non-reasoning model)
- Simple query → search → return results
- Fast but limited intelligence
- No internal planning or analysis

### **After: Agentic Search with Reasoning**
- Uses `gpt-5` (reasoning model)
- Model actively manages the search process
- Can perform multiple searches
- Analyzes results and decides whether to keep searching
- More thorough and intelligent event discovery

---

## 📊 Comparison

| Feature | Non-Reasoning Search | Agentic Search |
|---------|---------------------|----------------|
| **Model** | `gpt-4o` | `gpt-5` |
| **Intelligence** | Basic | Advanced reasoning |
| **Search Strategy** | Single pass | Multi-step planning |
| **Result Quality** | Good | Excellent |
| **Latency** | Fast (~5-10s) | Slower (~15-30s) |
| **Use Case** | Quick lookups | Comprehensive discovery |

---

## ⚙️ Configuration

### **Environment Variables** (`.env`)

```bash
# Model Selection
MODEL_NAME="gpt-5"              # Use gpt-5 for agentic search
                                # Or "gpt-4o" for fast non-reasoning search

# Reasoning Effort (controls depth and latency)
REASONING_EFFORT="medium"       # Options: "minimal", "low", "medium", "high", "xhigh"
                                # minimal = fastest, least thorough
                                # low = faster, less thorough
                                # medium = balanced (recommended)
                                # high = slower, more comprehensive
                                # xhigh = slowest, most comprehensive
```

---

## 🎯 Benefits of Agentic Search

### 1. **Multi-Step Search Strategy**
The model can:
- Perform initial broad searches
- Analyze results
- Conduct follow-up searches for more details
- Cross-reference information

### 2. **Intelligent Source Selection**
The model knows to check:
- Official event platforms (Eventbrite, Meetup, Luma)
- London-specific event aggregators
- Venue websites
- Organizer pages

### 3. **Better Date Verification**
- Can search for additional information if dates are unclear
- Cross-references multiple sources
- More reliable future event filtering

### 4. **Quality Over Speed**
- Takes longer but finds more relevant events
- Better at understanding context
- More accurate event details

---

## 🔧 Technical Implementation

### **Files Modified:**

1. **`config.py`**
   - Added `REASONING_EFFORT` configuration
   - Updated `MODEL_NAME` default to `gpt-5`
   - Enhanced prompt for agentic search with search strategy guidance

2. **`openai_client.py`**
   - Added `reasoning_effort` parameter to API call
   - Imported `REASONING_EFFORT` from config
   - Added logging to show reasoning effort being used

3. **`.env`**
   - Added `MODEL_NAME` and `REASONING_EFFORT` configuration options

---

## 🚀 Usage

### **Run with Default Settings (Medium Reasoning)**
```bash
python main.py
```

### **Adjust Reasoning Effort**

For **faster** searches (less thorough):
```bash
# In .env
REASONING_EFFORT="low"
```

For **most comprehensive** searches (slower):
```bash
# In .env
REASONING_EFFORT="high"
```

For **maximum depth** (slowest):
```bash
# In .env
REASONING_EFFORT="xhigh"
```

### **Switch Back to Non-Reasoning Search**

If you need faster results and don't need the extra intelligence:
```bash
# In .env
MODEL_NAME="gpt-4o"
# REASONING_EFFORT is ignored for non-reasoning models
```

---

## 📈 Expected Improvements

With agentic search, you should see:
- ✅ More events discovered per query
- ✅ Better quality event information
- ✅ More accurate date filtering
- ✅ Better coverage of different event platforms
- ⏱️ Longer search times (15-30s vs 5-10s)

---

## 💡 Recommendations

- **For daily automated runs**: Use `REASONING_EFFORT="medium"` (balanced)
- **For comprehensive one-time searches**: Use `REASONING_EFFORT="high"`
- **For deep research**: Use `REASONING_EFFORT="xhigh"` (slowest, most thorough)
- **For quick testing**: Use `REASONING_EFFORT="low"` or switch to `gpt-4o`

---

## 🧪 Testing

Run the system and observe the new output:

```bash
python main.py
```

You'll see:
```
Searching for events with query: 'upcoming London AI hackathons'
Using agentic search with gpt-5 (reasoning level: medium)
```

The search will take longer, but you should get more comprehensive and accurate results!

---

## 📚 Related Documentation

- [OpenAI Agentic Search Documentation](https://platform.openai.com/docs/guides/web-search)
- `PROCESS_FLOW.md` - System architecture
- `ARCHITECTURE.md` - Visual diagrams

