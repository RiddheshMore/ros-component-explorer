# 📊 Evaluation Framework# Semantic Search Evaluation Framework for ROS Component Explorer



This directory contains the evaluation framework for the ROS Component Explorer's hybrid semantic search system.## Overview



## 📁 StructureThis evaluation framework provides comprehensive testing and validation for the semantic querying capabilities of the ROS Component Explorer. It includes multiple evaluation methodologies to assess search quality, user experience, and system performance.



```## Evaluation Components

evaluation/

├── README.md (this file)### 1. Benchmark Suite (`benchmark_suite.py`)

└── context_aware_evaluation/

    ├── context_aware_queries_dataset.json  # 30 test queries**Purpose**: Systematic evaluation using standard information retrieval metrics

    ├── run_context_aware_evaluation.py     # Evaluation script

    └── results/                             # Evaluation outputs (gitignored)**Features**:

```- Ground truth dataset with curated query-result pairs

- Precision, Recall, F1-Score calculations

## 🎯 Context-Aware Evaluation- NDCG (Normalized Discounted Cumulative Gain) for ranking quality

- Mean Average Precision (MAP) across query sets

### Dataset Overview- Response time measurements

- Comparative analysis across multiple search methods

The evaluation uses 30 carefully curated context-aware queries that simulate real-world ROS 2 package discovery scenarios.

**Ground Truth Dataset**:

#### Query Types Distribution- 10 representative ROS component queries

- Manually curated relevant components for each query

| Query Type | Count | Description |- Covers navigation, SLAM, perception, control, and sensor domains

|------------|-------|-------------|- Expandable with additional queries and domains

| **Integration Compatibility** | 9 | Finding packages that work together |

| **Dependency Based** | 7 | Identifying required dependencies |**Metrics Evaluated**:

| **Hardware Constrained** | 6 | Hardware-specific package discovery |- **Precision**: Fraction of retrieved components that are relevant

| **Feature Addition** | 6 | Finding complementary features |- **Recall**: Fraction of relevant components that are retrieved  

| **Replacement Alternative** | 2 | Finding alternative packages |- **F1-Score**: Harmonic mean of precision and recall

- **NDCG@k**: Quality of ranking considering position

### Example Queries- **Response Time**: Search latency in seconds



**Integration Compatibility**### 2. User Study Simulation (`user_study_simulation.py`)

```

"I'm using nav2 for autonomous navigation. **Purpose**: Simulate realistic user behavior and search patterns

What localization packages are compatible with nav2?"

**User Profiles**:

Expected: robot_localization, beluga_amcl, slam_toolbox- **Robotics Student**: Beginner, natural language queries, basic domains

```- **ROS Developer**: Intermediate, mixed query styles, core ROS functionality

- **Research Engineer**: Expert, keyword queries, advanced topics

**Hardware Constrained**- **System Integrator**: Expert, practical integration focus

```- **Hobbyist Maker**: Beginner, simple navigation and sensors

"I have a Velodyne VLP-16 LIDAR. 

What SLAM packages support this sensor?"**Simulated Behaviors**:

- Query generation based on user expertise and domain focus

Expected: slam_toolbox, velodyne_pointcloud, cartographer_ros- Click-through simulation with position bias

```- Session satisfaction scoring

- Realistic timing and interaction patterns

**Dependency Based**

```**Outputs**:

"I'm using robot_localization for sensor fusion. - User satisfaction scores by profile type

What IMU drivers can provide input to it?"- Click-through rates and engagement metrics

- Most common query patterns

Expected: phidgets_spatial, microstrain_inertial, adi_imu- Performance differences across user segments

```

### 3. A/B Testing Framework (`ab_testing.py`)

## 🚀 Running Evaluation

**Purpose**: Statistical comparison of different search methods

### Basic Evaluation

```bash**Test Configurations**:

cd evaluation/context_aware_evaluation- Vector vs Text Search (relevance, satisfaction, CTR)

python run_context_aware_evaluation.py- Hybrid vs Pure Vector Search

```- NLP Enhanced vs Basic approaches

- Multiple success metrics per comparison

### Output Metrics

**Statistical Analysis**:

The evaluation script measures:- Paired t-tests for significance testing

- Effect size calculations (Cohen's d)

| Metric | Description | Range |- Confidence intervals for performance differences

|--------|-------------|-------|- Multiple testing correction

| **F1@10** | Harmonic mean of precision and recall | 0.0 - 1.0 |

| **NDCG@10** | Normalized Discounted Cumulative Gain | 0.0 - 1.0 |**Success Metrics**:

| **MAP@10** | Mean Average Precision | 0.0 - 1.0 |- **Relevance Score**: Term overlap and semantic matching

| **Success@10** | Percentage of queries with ≥1 relevant result | 0% - 100% |- **User Satisfaction**: Simulated based on result quality and diversity

| **Latency** | Average query execution time | milliseconds |- **Click-Through Rate**: Position-biased click probability



### Current Results## Usage



Based on 30 context-aware queries:### Running the Complete Evaluation Suite



| Method | F1@10 | NDCG@10 | MAP@10 | Success@10 | Latency |```bash

|--------|-------|---------|--------|------------|---------|# Run benchmark evaluation

| **Keyword (BM25)** | 0.171 | 0.345 | 0.255 | 70.00% | 25ms |cd evaluation/

| **Vector (BERT)** | 0.187 | 0.407 | 0.316 | **76.67%** | **17ms** |python benchmark_suite.py

| **Hybrid (α=0.5)** | 0.182 | 0.401 | 0.315 | 73.33% | 51ms |

| **Hybrid (α=0.7)** | 0.187 | 0.406 | 0.316 | 76.67% | 51ms |# Run user study simulation  

python user_study_simulation.py

### Key Findings

# Run A/B testing (requires scipy)

✅ **Vector search outperforms keyword search**pip install scipy

- 6.7% higher success rate (76.67% vs 70%)python ab_testing.py

- 32% faster latency (17ms vs 25ms)```

- 18% better NDCG@10 (0.407 vs 0.345)

### Individual Evaluations

⚡ **Hybrid search adds robustness but increases latency**

- Combines strengths of both approaches```bash

- Best α value depends on use case# Just benchmark metrics

- 3x latency overhead due to dual processingpython -c "

from evaluation.benchmark_suite import ROSComponentBenchmark

## 📈 Performance Analysisbenchmark = ROSComponentBenchmark('data/mobile_robot_packages_hierarchical.ttl')

results = benchmark.run_comparative_benchmark(['vector_search', 'text_search'])

### Latency Breakdownprint(results)

"

**Vector Search (17ms total)**

- BERT encoding: 7.3ms# Just user study

- KNN search: 7.4mspython -c "

- Result processing: 2.3msfrom evaluation.user_study_simulation import UserStudySimulator  

simulator = UserStudySimulator('data/mobile_robot_packages_hierarchical.ttl')

**Keyword Search (25ms total)**results = simulator.run_user_study(num_sessions_per_profile=5)

- Query parsing: 8.2msprint(results['overall_stats'])

- BM25 scoring: 12.1ms"

- Result ranking: 4.7ms```



### Success Rate by Query Type## Validation Results



| Query Type | Keyword | Vector | Improvement |### Search Method Performance (Example)

|------------|---------|--------|-------------|

| Integration Compatibility | 66.7% | 77.8% | +11.1% || Method | Precision | Recall | F1-Score | NDCG@10 | Response Time |

| Dependency Based | 71.4% | 85.7% | +14.3% ||--------|-----------|--------|----------|---------|---------------|

| Hardware Constrained | 66.7% | 66.7% | 0% || Vector Search | 0.742 | 0.681 | 0.710 | 0.785 | 0.145s |

| Feature Addition | 83.3% | 83.3% | 0% || Hybrid Search | 0.768 | 0.695 | 0.729 | 0.801 | 0.167s |

| Replacement Alternative | 50.0% | 50.0% | 0% || Text Search | 0.634 | 0.592 | 0.612 | 0.673 | 0.089s |

| NLP Enhanced | 0.751 | 0.703 | 0.726 | 0.793 | 0.201s |

## 🔧 Customization

### User Study Results (Example)

### Adding New Queries

| User Type | Satisfaction | CTR | Queries/Session | Preferred Method |

Edit `context_aware_queries_dataset.json`:|-----------|-------------|-----|-----------------|------------------|

| Beginner | 0.73 | 0.42 | 4.2 | Natural Language |

```json| Intermediate | 0.81 | 0.38 | 7.6 | Hybrid Search |

{| Expert | 0.85 | 0.35 | 11.3 | Vector + Keywords |

  "query_text": "Your query here",

  "relevant_packages": ["package1", "package2"],### A/B Testing Significance

  "context": {

    "query_type": "integration_compatibility",- **Vector vs Text**: Significant improvement (p=0.003, d=0.67)

    "existing_packages": ["navigation2"],- **Hybrid vs Vector**: Marginal improvement (p=0.048, d=0.23)  

    "use_case": "mobile robot navigation"- **NLP vs Hybrid**: No significant difference (p=0.142)

  },

  "rationale": "Why these packages are relevant"## Extending the Framework

}

```### Adding New Ground Truth Queries



### Modifying Evaluation Parameters```python

from evaluation.benchmark_suite import GroundTruthDataset

In `run_context_aware_evaluation.py`:

- `k = 10`: Number of results to retrievedataset = GroundTruthDataset()

- `alpha_values = [0.5, 0.7, 1.0]`: Hybrid search weights to testdataset.add_query(

- `warmup_queries = 2`: Number of warmup queries before timing    query="multi-robot formation control",

    query_type="coordination", 

## 📊 Result Files    relevant_components={"multi_robot_msgs", "formation_control", "leader_follower"}

)

Evaluation results are saved with timestamps:dataset.save_to_file("custom_ground_truth.json")

``````

context_aware_eval_results_YYYYMMDD_HHMMSS.json

```### Creating Custom User Profiles



Structure:```python

```jsonfrom evaluation.user_study_simulation import UserProfile

{

  "dataset": "context_aware_queries_dataset.json",custom_profile = UserProfile(

  "timestamp": "2024-11-16 09:30:00",    user_type="industrial_engineer",

  "methods": [    experience_level="expert",

    {    preferred_query_style="keyword",

      "name": "keyword",    domain_focus=["safety", "industrial_automation"],

      "aggregate_metrics": {...},    avg_session_length=15,

      "per_query_metrics": [...]    query_complexity="complex"

    },)

    ...```

  ]

}### Adding New A/B Tests

```

```python

## 🎓 Citationfrom evaluation.ab_testing import ABTestConfig



If you use this evaluation framework, please cite:test_config = ABTestConfig(

```    test_name="Custom Search Comparison",

ROS Component Explorer: Hybrid Semantic Search for ROS 2 Package Discovery    method_a="new_method",

Riddhesh More, 2024    method_b="baseline_method",

IROS 2024 Presentation    test_queries=custom_queries,

```    success_metric="custom_metric"

)

## 📝 Notes```



- Evaluation uses model warmup (2 queries) to exclude initialization overhead## Benchmark Dataset Details

- Results are averaged across all 30 queries

- GPU acceleration recommended for faster vector encoding### Query Categories and Examples

- Solr must be running on localhost:8984 for evaluation

**Navigation Queries**:
- "autonomous navigation for mobile robots" → move_base, nav2, navigation_stack
- "obstacle detection and avoidance" → laser_filters, costmap_2d, obstacle_detector

**SLAM Queries**:
- "SLAM algorithms for indoor mapping" → gmapping, hector_slam, slam_toolbox  
- "visual SLAM for robots" → rtabmap, orb_slam, stereo_slam

**Perception Queries**:
- "camera and vision processing" → image_transport, cv_bridge, image_proc
- "LiDAR data processing" → laser_geometry, pointcloud_to_laserscan

**Control Queries**:
- "motor control and joint states" → joint_state_publisher, controller_manager
- "path planning for dynamic environments" → ompl, moveit, teb_local_planner

### Relevance Criteria

Components are considered relevant if they:
1. Directly implement the requested functionality
2. Are commonly used together with core components  
3. Provide essential supporting functionality
4. Are standard solutions in the ROS ecosystem

## Statistical Validation

### Power Analysis

- Minimum effect size detectable: Cohen's d = 0.5
- Statistical power: 80% 
- Significance level: α = 0.05
- Minimum sample size: 30 queries per test

### Multiple Testing Correction

When running multiple A/B tests, apply Bonferroni correction:
```python
adjusted_alpha = 0.05 / number_of_tests
```

## Integration with Continuous Evaluation

### Automated Testing Pipeline

```bash
#!/bin/bash
# evaluation/run_continuous_eval.sh

echo "Running continuous evaluation pipeline..."

# Run benchmarks
python benchmark_suite.py > logs/benchmark_$(date +%Y%m%d).log 2>&1

# Run user study 
python user_study_simulation.py > logs/user_study_$(date +%Y%m%d).log 2>&1

# Run A/B tests if changes detected
if [ -f "search_methods_updated.flag" ]; then
    python ab_testing.py > logs/ab_test_$(date +%Y%m%d).log 2>&1
    rm search_methods_updated.flag
fi

echo "Evaluation complete. Check logs/ for detailed results."
```

### Performance Monitoring

```python
# evaluation/performance_monitor.py
import time
from pathlib import Path

def monitor_search_performance():
    """Monitor search performance over time."""
    benchmark = ROSComponentBenchmark(ttl_file)
    
    while True:
        # Run lightweight benchmark
        results = benchmark.benchmark_search_method("vector_search", k=5)
        
        # Log results
        timestamp = time.time()
        log_entry = {
            "timestamp": timestamp,
            "avg_precision": results.avg_precision,
            "avg_response_time": results.avg_response_time
        }
        
        # Alert if performance degrades
        if results.avg_precision < 0.6 or results.avg_response_time > 1.0:
            send_alert(log_entry)
        
        time.sleep(3600)  # Check hourly
```

This comprehensive evaluation framework ensures that semantic search improvements are validated scientifically and user experience is continuously monitored and optimized.

## Output Files

All evaluation results are saved to the `evaluation/` directory:

- `benchmark_report_YYYYMMDD_HHMMSS.xlsx` - Detailed benchmark results
- `user_study_results_YYYYMMDD_HHMMSS.json` - User study simulation data  
- `ab_test_report_YYYYMMDD_HHMMSS.md` - A/B testing markdown report
- `ab_test_results_YYYYMMDD_HHMMSS.json` - Raw A/B test data
- `ground_truth_dataset.json` - Reusable ground truth queries