def split_large_task(task_description: str, max_size: int = 10) -> List[str]:
    """Split large tasks into smaller chunks to avoid tool limit"""
    
    # Common task patterns that trigger high tool usage
    high_usage_patterns = [
        "comprehensive audit",
        "full system check", 
        "complete validation",
        "end-to-end test"
    ]
    
    if any(pattern in task_description.lower() for pattern in high_usage_patterns):
        return [
            "Check system status only",
            "Validate Docker containers only", 
            "Test Langflow connectivity only",
            "Review security status only",
            "Generate summary report only"
        ]
    
    return [task_description]  # Return as-is if not complex

def execute_task_sequence(tasks: List[str], delay_between: int = 30):
    """Execute tasks in sequence with delays"""
    for i, task in enumerate(tasks):
        print(f"🔄 Executing task {i+1}/{len(tasks)}: {task}")
        
        # Your task execution logic here
        result = throttler.execute_with_throttle(lambda: f"Completed: {task}")
        print(f"✅ {result}")
        
        if i < len(tasks) - 1:  # Don't delay after last task
            print(f"⏳ Waiting {delay_between}s before next task...")
            time.sleep(delay_between)