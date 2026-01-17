/// ============================================================================
/// VULNERABLE TOKEN CONTRACT - FOR DEMONSTRATION PURPOSES ONLY
/// ============================================================================
/// 
/// This contract contains INTENTIONAL VULNERABILITIES designed to showcase
/// the AI Compliance Agent's detection capabilities.
/// 
/// DO NOT USE THIS CODE IN PRODUCTION!
/// 
/// Vulnerabilities included:
/// 1. Entry function without signer verification
/// 2. Capability struct with 'copy' ability (can be duplicated)
/// 3. Public functions that should be private
/// 4. Missing access control on sensitive operations
/// ============================================================================

module demo::vulnerable_token {
    use std::signer;
    use aptos_framework::coin;
    use aptos_framework::account;

    /// ERROR CODES
    const E_NOT_INITIALIZED: u64 = 1;
    const E_INSUFFICIENT_BALANCE: u64 = 2;

    // =========================================================================
    // VULNERABILITY #1: Capability with 'copy' ability
    // 
    // This allows the admin capability to be freely duplicated, which defeats
    // the purpose of having a capability-based access control.
    // A real implementation should NOT have 'copy' on capability structs.
    // =========================================================================
    struct AdminCapability has copy, store, key {
        can_mint: bool,
        can_burn: bool,
        can_freeze: bool,
    }

    // =========================================================================
    // VULNERABILITY #2: Capability with 'store' ability
    // 
    // This allows the capability to be stored anywhere, potentially leaked
    // to untrusted storage locations.
    // =========================================================================
    struct MinterCapability has store, key {
        mint_limit: u64,
    }

    /// Token balance storage
    struct TokenStore has key {
        balance: u64,
        frozen: bool,
    }

    /// Global token info
    struct TokenInfo has key {
        total_supply: u64,
        name: vector<u8>,
        symbol: vector<u8>,
    }

    // =========================================================================
    // VULNERABILITY #3: Entry function WITHOUT signer parameter
    // 
    // This is a CRITICAL vulnerability! Any user can call this function
    // and mint tokens to any address without authorization.
    // The compliance agent should flag this as HIGH severity.
    // =========================================================================
    public entry fun mint_to_anyone(
        recipient: address,
        amount: u64
    ) acquires TokenStore, TokenInfo {
        // VULNERABLE: No authorization check! Anyone can mint!
        if (!exists<TokenStore>(recipient)) {
            abort E_NOT_INITIALIZED
        };
        
        let store = borrow_global_mut<TokenStore>(recipient);
        store.balance = store.balance + amount;
        
        let info = borrow_global_mut<TokenInfo>(@demo);
        info.total_supply = info.total_supply + amount;
    }

    // =========================================================================
    // VULNERABILITY #4: Entry function for burning without proper checks
    // 
    // This allows burning tokens from ANY address without the owner's consent.
    // =========================================================================
    public entry fun burn_from_anyone(
        target: address,
        amount: u64
    ) acquires TokenStore, TokenInfo {
        // VULNERABLE: No authorization - can burn anyone's tokens!
        let store = borrow_global_mut<TokenStore>(target);
        assert!(store.balance >= amount, E_INSUFFICIENT_BALANCE);
        store.balance = store.balance - amount;
        
        let info = borrow_global_mut<TokenInfo>(@demo);
        info.total_supply = info.total_supply - amount;
    }

    // =========================================================================
    // VULNERABILITY #5: Freeze function without authorization
    // 
    // Can freeze any user's account without proper authority.
    // =========================================================================
    public entry fun freeze_account(target: address) acquires TokenStore {
        // VULNERABLE: Anyone can freeze any account!
        let store = borrow_global_mut<TokenStore>(target);
        store.frozen = true;
    }

    // =========================================================================
    // SAFE FUNCTION - For comparison
    // 
    // This function properly uses a signer to verify the caller.
    // =========================================================================
    public entry fun transfer(
        sender: &signer,
        recipient: address,
        amount: u64
    ) acquires TokenStore {
        let sender_addr = signer::address_of(sender);
        
        // Check sender has enough balance
        let sender_store = borrow_global_mut<TokenStore>(sender_addr);
        assert!(!sender_store.frozen, 3);
        assert!(sender_store.balance >= amount, E_INSUFFICIENT_BALANCE);
        sender_store.balance = sender_store.balance - amount;
        
        // Add to recipient
        let recipient_store = borrow_global_mut<TokenStore>(recipient);
        assert!(!recipient_store.frozen, 4);
        recipient_store.balance = recipient_store.balance + amount;
    }

    /// Initialize the token (SAFE - uses signer)
    public entry fun initialize(admin: &signer) {
        let admin_addr = signer::address_of(admin);
        
        move_to(admin, TokenInfo {
            total_supply: 0,
            name: b"Vulnerable Token",
            symbol: b"VULN",
        });
        
        move_to(admin, TokenStore {
            balance: 0,
            frozen: false,
        });
        
        // Create admin capability (but it has copy ability - vulnerable!)
        move_to(admin, AdminCapability {
            can_mint: true,
            can_burn: true,
            can_freeze: true,
        });
    }

    // =========================================================================
    // PUBLIC FUNCTION THAT SHOULD BE PRIVATE
    // 
    // This internal helper is marked public, exposing implementation details.
    // =========================================================================
    public fun get_raw_balance(addr: address): u64 acquires TokenStore {
        borrow_global<TokenStore>(addr).balance
    }
}
