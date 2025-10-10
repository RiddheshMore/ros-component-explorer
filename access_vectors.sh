#!/bin/bash
# Solr Vector Access Commands

echo "🔍 Apache Solr Vector Access Guide"
echo "=================================="

SOLR_URL="http://localhost:8984/solr/ros_explorer"

echo ""
echo "1. 📊 Check if vectors exist:"
curl -s "${SOLR_URL}/select?q=vector:*&rows=0" | jq '.response.numFound'

echo ""
echo "2. 🎯 Get a specific component with vector:"
echo "curl \"${SOLR_URL}/select?q=id:COMPONENT_ID&fl=id,name,vector\""

echo ""
echo "3. 📋 List first 5 components with vectors:"
curl -s "${SOLR_URL}/select?q=vector:*&fl=id,name,vector&rows=5" | jq '.response.docs[]'

echo ""
echo "4. 🔧 Check vector field schema:"
curl -s "${SOLR_URL}/schema/fields/vector" | jq '.'

echo ""
echo "5. 📈 Get vector statistics:"
curl -s "${SOLR_URL}/select?q=*:*&rows=0&facet=true&facet.field=vector" | jq '.facet_counts'

echo ""
echo "6. 🌐 Access Solr Admin UI:"
echo "   Open: http://localhost:8984/solr/#/ros_explorer/query"
echo "   Query: vector:*"
echo "   Fields: id,name,vector"

echo ""
echo "7. 🐍 Python programmatic access:"
echo "   Run: python vector_access_utility.py"
