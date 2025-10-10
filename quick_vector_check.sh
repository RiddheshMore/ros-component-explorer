#!/bin/bash
# Quick Vector Check Script
# Simple one-liner commands to verify vector storage

echo "🔍 Quick Vector Verification Commands"
echo "======================================"
echo

echo "1. 📊 Check total documents:"
curl -s "http://localhost:8984/solr/ros_explorer/select?q=*:*&rows=0&wt=json" | jq '.response.numFound'
echo

echo "2. 📈 Count documents with vectors:"
curl -s "http://localhost:8984/solr/ros_explorer/select?q=vector:*&rows=0&wt=json" | jq '.response.numFound'
echo

echo "3. 📏 Check vector dimensions (first 3 components):"
curl -s "http://localhost:8984/solr/ros_explorer/select?q=vector:*&fl=id,vector&rows=3&wt=json" | jq '.response.docs[] | {id: .id, vector_length: (.vector | length)}'
echo

echo "4. 🎯 Verify vector field exists:"
curl -s "http://localhost:8984/solr/ros_explorer/schema/fields/vector" | jq '.field.type' 2>/dev/null || echo "Vector field not found"
echo

echo "5. 📋 Quick summary:"
TOTAL=$(curl -s "http://localhost:8984/solr/ros_explorer/select?q=*:*&rows=0&wt=json" | jq '.response.numFound')
WITH_VECTORS=$(curl -s "http://localhost:8984/solr/ros_explorer/select?q=vector:*&rows=0&wt=json" | jq '.response.numFound')

if [ "$WITH_VECTORS" -gt 0 ]; then
    PERCENTAGE=$(echo "scale=1; $WITH_VECTORS * 100 / $TOTAL" | bc)
    echo "✅ $WITH_VECTORS out of $TOTAL components have vectors (${PERCENTAGE}%)"
else
    echo "❌ No vectors found in $TOTAL components"
fi
