
# Model Notes

## 1. LogisticRegression

### Why it fits

### Strength

### Limitation

### Key hyperparameters

- class_weight: balanced
- C: 1
- solver: lbfgs
- Preprocessing: median imputation and feature scaling

## 2. RandomForest

### Why it fits

### Strength

### Limitation

### Key hyperparameters

- n_estimators: 200
- max_depth: 20
- min_samples_leaf: 5

## 3. LightGBM

### Why it fits

### Strength

### Limitation

### Key hyperparameters

- learning_rate: 0.0112407688
- num_leaves: 197
- min_child_samples: 12
- subsample: 0.8312611422
- colsample_bytree: 0.6558555380
- reg_lambda: 0.1203017887
- reg_alpha: 0.0002364189
- n_estimators: 1000

## 4. XGBoost

### Why it fits

### Strength

### Limitation

### Key hyperparameters

- n_estimators: up to 500 boosting rounds
- learning_rate: 0.05
- max_depth: 8
- tree_method: hist
- Early stopping rounds: 30
- Training configuration: 10% group holdout

## 5. MLP

### Why it fits

### Strength

### Limitation

### Key hyperparameters

- hidden_layer_sizes: (64, 32)
- activation: relu
- solver: adam
- early_stopping: True
