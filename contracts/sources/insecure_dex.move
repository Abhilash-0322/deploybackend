/// ============================================================================
/// INSECURE DEX CONTRACT - FOR DEMONSTRATION PURPOSES ONLY
/// ============================================================================
/// 
/// This contract simulates a decentralized exchange with INTENTIONAL SECURITY
/// FLAWS designed to showcase vulnerability detection.
/// 
/// DO NOT USE THIS CODE IN PRODUCTION!
/// 
/// Vulnerabilities included:
/// 1. Entry functions without signer (anyone can swap/withdraw)
/// 2. Unconstrained generic types
/// 3. Excessive friend modules
/// 4. Logic flaws in swap calculation
/// ============================================================================

module demo::insecure_dex {
    use std::signer;

    // =========================================================================
    // VULNERABILITY: Too many friend declarations
    // 
    // Having excessive friends expands the trust boundary significantly.
    // This should be flagged as a medium-severity issue.
    // =========================================================================
    friend demo::vulnerable_token;
    friend demo::risky_nft;
    friend demo::unsafe_staking;
    friend demo::bad_governance;
    friend demo::weak_oracle;
    friend demo::flawed_lending;

    /// Pool storage
    struct LiquidityPool has key {
        reserve_a: u64,
        reserve_b: u64,
        total_lp_tokens: u64,
        fee_percentage: u64,
    }

    /// User's LP token balance
    struct LPTokenStore has key {
        balance: u64,
    }

    // =========================================================================
    // VULNERABILITY: Swap without authorization
    // 
    // CRITICAL: Anyone can execute swaps on behalf of any user!
    // No signer verification means funds can be stolen.
    // =========================================================================
    public entry fun swap_tokens_unprotected(
        user_address: address,
        amount_in: u64,
        min_amount_out: u64
    ) acquires LiquidityPool {
        // VULNERABLE: No verification that caller is the user!
        let pool = borrow_global_mut<LiquidityPool>(@demo);
        
        // Simplified swap logic (also vulnerable to manipulation)
        let amount_out = (amount_in * pool.reserve_b) / pool.reserve_a;
        
        // No slippage protection check is actually enforced!
        // The min_amount_out is ignored
        pool.reserve_a = pool.reserve_a + amount_in;
        pool.reserve_b = pool.reserve_b - amount_out;
    }

    // =========================================================================
    // VULNERABILITY: Withdraw liquidity without ownership check
    // 
    // Anyone can withdraw liquidity from any user's position!
    // =========================================================================
    public entry fun withdraw_liquidity_unsafe(
        provider_address: address,
        lp_amount: u64
    ) acquires LiquidityPool, LPTokenStore {
        // VULNERABLE: Not checking if caller owns the LP tokens!
        let lp_store = borrow_global_mut<LPTokenStore>(provider_address);
        lp_store.balance = lp_store.balance - lp_amount;
        
        let pool = borrow_global_mut<LiquidityPool>(@demo);
        pool.total_lp_tokens = pool.total_lp_tokens - lp_amount;
    }

    // =========================================================================
    // VULNERABILITY: Emergency function without proper access control
    // 
    // This "emergency" function can drain the entire pool!
    // =========================================================================
    public entry fun emergency_drain(destination: address) acquires LiquidityPool {
        // CRITICAL VULNERABILITY: Anyone can drain the pool!
        let pool = borrow_global_mut<LiquidityPool>(@demo);
        pool.reserve_a = 0;
        pool.reserve_b = 0;
        // Tokens would be sent to destination (simulated)
    }

    // =========================================================================
    // SAFE FUNCTION - For comparison
    // =========================================================================
    public entry fun add_liquidity_safe(
        provider: &signer,
        amount_a: u64,
        amount_b: u64
    ) acquires LiquidityPool, LPTokenStore {
        let provider_addr = signer::address_of(provider);
        
        let pool = borrow_global_mut<LiquidityPool>(@demo);
        pool.reserve_a = pool.reserve_a + amount_a;
        pool.reserve_b = pool.reserve_b + amount_b;
        
        let lp_tokens_minted = amount_a; // Simplified
        pool.total_lp_tokens = pool.total_lp_tokens + lp_tokens_minted;
        
        if (!exists<LPTokenStore>(provider_addr)) {
            move_to(provider, LPTokenStore { balance: lp_tokens_minted });
        } else {
            let store = borrow_global_mut<LPTokenStore>(provider_addr);
            store.balance = store.balance + lp_tokens_minted;
        }
    }

    /// Initialize the pool
    public entry fun initialize_pool(admin: &signer) {
        move_to(admin, LiquidityPool {
            reserve_a: 0,
            reserve_b: 0,
            total_lp_tokens: 0,
            fee_percentage: 30, // 0.3%
        });
    }

    // =========================================================================
    // VULNERABILITY: Public view function exposing sensitive data
    // =========================================================================
    public fun get_pool_secrets(): (u64, u64, u64) acquires LiquidityPool {
        let pool = borrow_global<LiquidityPool>(@demo);
        (pool.reserve_a, pool.reserve_b, pool.fee_percentage)
    }
}
