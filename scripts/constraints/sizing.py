from config import get_config
from logger import logger

config = get_config()

def sizing_constraints(usdc_size: float) -> float:
    """
    Scales a trader's USDC size by STAKE_WHALE_PCT. No minimum — every trade
    is copied. Caps at STAKE_MAX.
    """
    sizing_factor = config.STAKE_WHALE_PCT
    new_size = usdc_size * sizing_factor

    if new_size > config.STAKE_MAX:
        logger.debug(f"Sized amount ${new_size:.2f} exceeds maximum stake ${config.STAKE_MAX}. Capping.")
        new_size = config.STAKE_MAX

    logger.info(f"Sizing: Target ${usdc_size} -> Bot ${new_size:.2f} ({sizing_factor*100}%)")
    return round(new_size, 2)

if __name__ == "__main__":
    print(f"Test 500:   {sizing_constraints(500)}")
    print(f"Test 10:    {sizing_constraints(10)}")
    print(f"Test 10000: {sizing_constraints(10000)}")
