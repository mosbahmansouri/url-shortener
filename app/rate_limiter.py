from fastapi import HTTPException

def rate_Limiter (cach,key_prefix : str, identifier:str , limit : int , window_second: int):
    """
    raise and error of too many requests if the user (identifier)
    
    has made more that limit requests to key prefix  within window seconds 
    """
    key = (f"ratelimit: {key_prefix}:{identifier}")
    current = cach.incr(key)
    if current == 1:
        cach.expire (key,window_second)

    if current > limit :
        ttl = cach.ttl(key )
        raise HTTPException (
            status_code= 429,
            detail="Too many requests,slow down",
            headers={"retry-after": str(ttl if ttl >10 else window_second)}

        )        
        
        

    











