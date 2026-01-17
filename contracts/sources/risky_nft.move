/// ============================================================================
/// RISKY NFT CONTRACT - FOR DEMONSTRATION PURPOSES ONLY
/// ============================================================================
/// 
/// This NFT contract contains INTENTIONAL VULNERABILITIES for demo purposes.
/// 
/// DO NOT USE THIS CODE IN PRODUCTION!
/// 
/// Vulnerabilities included:
/// 1. NFT transfer without owner verification
/// 2. Royalty bypass vulnerability
/// 3. Metadata manipulation without authorization
/// ============================================================================

module demo::risky_nft {
    use std::signer;
    use std::string::String;
    use std::vector;

    /// NFT data structure
    struct NFT has key, store {
        id: u64,
        name: String,
        uri: String,
        creator: address,
        royalty_percentage: u64,
    }

    /// Collection info
    struct Collection has key {
        name: String,
        total_minted: u64,
        max_supply: u64,
    }

    /// NFT ownership tracking
    struct NFTOwnership has key {
        owned_nfts: vector<u64>,
    }

    // =========================================================================
    // VULNERABILITY: Transfer NFT without owner verification
    // 
    // CRITICAL: Anyone can transfer any NFT to themselves!
    // =========================================================================
    public entry fun transfer_nft_unsafe(
        nft_id: u64,
        from: address,
        to: address
    ) acquires NFTOwnership {
        // VULNERABLE: No check that caller is the owner!
        let from_ownership = borrow_global_mut<NFTOwnership>(from);
        
        // Remove from sender (without verification!)
        let (found, index) = vector::index_of(&from_ownership.owned_nfts, &nft_id);
        if (found) {
            vector::remove(&mut from_ownership.owned_nfts, index);
        };
        
        // Add to recipient
        let to_ownership = borrow_global_mut<NFTOwnership>(to);
        vector::push_back(&mut to_ownership.owned_nfts, nft_id);
    }

    // =========================================================================
    // VULNERABILITY: Burn NFT without owner consent
    // =========================================================================
    public entry fun burn_nft_unprotected(
        owner_address: address,
        nft_id: u64
    ) acquires NFTOwnership {
        // VULNERABLE: Anyone can burn anyone's NFT!
        let ownership = borrow_global_mut<NFTOwnership>(owner_address);
        let (found, index) = vector::index_of(&ownership.owned_nfts, &nft_id);
        if (found) {
            vector::remove(&mut ownership.owned_nfts, index);
        };
    }

    // =========================================================================
    // VULNERABILITY: Modify NFT metadata without authorization
    // 
    // Anyone can change the URI of any NFT (could point to malicious content)
    // =========================================================================
    public entry fun update_metadata_unsafe(
        nft_id: u64,
        new_uri: String
    ) {
        // VULNERABLE: No authorization check!
        // In reality this would update the NFT's URI
        // This could be used to replace legitimate artwork with scams
        let _ = nft_id;
        let _ = new_uri;
    }

    // =========================================================================
    // VULNERABILITY: Free mint without limits
    // =========================================================================
    public entry fun free_mint_unlimited(recipient: address) acquires Collection, NFTOwnership {
        // VULNERABLE: No signer, no payment, no limits!
        let collection = borrow_global_mut<Collection>(@demo);
        collection.total_minted = collection.total_minted + 1;
        
        // Note: This bypasses max_supply check intentionally for demo
        
        if (!exists<NFTOwnership>(recipient)) {
            // Can't move_to without signer - this would fail
            // But the vulnerability pattern is demonstrated
        };
    }

    // =========================================================================
    // SAFE FUNCTION - For comparison
    // =========================================================================
    public entry fun transfer_nft_safe(
        owner: &signer,
        nft_id: u64,
        to: address
    ) acquires NFTOwnership {
        let owner_addr = signer::address_of(owner);
        
        // Verify ownership
        let ownership = borrow_global_mut<NFTOwnership>(owner_addr);
        let (found, index) = vector::index_of(&ownership.owned_nfts, &nft_id);
        assert!(found, 1); // Must own the NFT
        
        vector::remove(&mut ownership.owned_nfts, index);
        
        let to_ownership = borrow_global_mut<NFTOwnership>(to);
        vector::push_back(&mut to_ownership.owned_nfts, nft_id);
    }

    /// Initialize collection (SAFE)
    public entry fun create_collection(creator: &signer, name: String, max_supply: u64) {
        move_to(creator, Collection {
            name,
            total_minted: 0,
            max_supply,
        });
    }
}
