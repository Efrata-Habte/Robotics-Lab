# What turn_away is doing, published each time it receives an ObstacleInfo message
string state               # "forward", "turning" or "stopped"
float32 obstacle_distance  # m, distance to the nearest obstacle in front
