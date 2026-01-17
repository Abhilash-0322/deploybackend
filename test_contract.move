module test::vulnerable_contract {
    use std::signer;

    // INTENTIONAL VULNERABILITY: Entry function without signer check
    public entry fun unsafe_transfer(amount: u64) {
        // Missing signer parameter - anyone can call this!
        // This is a critical security issue
    }

    struct AdminCap has copy, store {
        // VULNERABILITY: Capability with copy ability
        power: u64
    }

    // VULNERABILITY: Public function that modifies state without proper authorization
    public fun modify_balance(addr: address, amount: u64) acquires Balance {
        let balance = borrow_global_mut<Balance>(addr);
        balance.value = amount;
    }

    struct Balance has key {
        value: u64
    }
}
