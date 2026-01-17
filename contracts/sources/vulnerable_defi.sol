// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * INTENTIONALLY VULNERABLE DeFi CONTRACT - FOR TESTING ONLY
 * 
 * This contract contains multiple critical vulnerabilities:
 * 1. tx.origin authentication bypass
 * 2. Reentrancy vulnerability
 * 3. Unprotected selfdestruct
 * 4. Integer overflow potential
 * 5. Timestamp manipulation
 */

contract VulnerableDeFiVault {
    mapping(address => uint256) public balances;
    mapping(address => uint256) public lockTime;
    address public owner;
    uint256 public totalLocked;
    
    event Deposit(address indexed user, uint256 amount);
    event Withdrawal(address indexed user, uint256 amount);
    
    constructor() {
        owner = msg.sender;
    }
    
    // CRITICAL: Using tx.origin for authorization
    // Vulnerable to phishing attacks
    modifier onlyOwner() {
        require(tx.origin == owner, "Not owner");
        _;
    }
    
    // Deposit funds with time lock
    function deposit(uint256 lockDuration) public payable {
        require(msg.value > 0, "Must deposit something");
        
        balances[msg.sender] += msg.value;
        totalLocked += msg.value;
        
        // MEDIUM: Using block.timestamp for time-sensitive logic
        lockTime[msg.sender] = block.timestamp + lockDuration;
        
        emit Deposit(msg.sender, msg.value);
    }
    
    // CRITICAL: Reentrancy vulnerability - state updated after external call
    function withdraw(uint256 amount) public {
        require(balances[msg.sender] >= amount, "Insufficient balance");
        
        // MEDIUM: Timestamp dependency
        require(block.timestamp >= lockTime[msg.sender], "Funds are locked");
        
        // CRITICAL: External call before state update (reentrancy)
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success, "Transfer failed");
        
        // State update happens AFTER external call
        balances[msg.sender] -= amount;
        totalLocked -= amount;
        
        emit Withdrawal(msg.sender, amount);
    }
    
    // HIGH: Using transfer() which can fail with smart contracts
    function emergencyWithdraw() public {
        uint256 balance = balances[msg.sender];
        require(balance > 0, "No balance");
        
        balances[msg.sender] = 0;
        totalLocked -= balance;
        
        // HIGH: transfer() has fixed gas limit
        payable(msg.sender).transfer(balance);
    }
    
    // HIGH: Delegatecall to user-controlled address
    function executeAction(address target, bytes memory data) public onlyOwner {
        // CRITICAL: delegatecall allows target to modify this contract's storage
        (bool success, ) = target.delegatecall(data);
        require(success, "Delegatecall failed");
    }
    
    // CRITICAL: Unprotected selfdestruct
    function destroy() public {
        // Anyone can call this and destroy the contract!
        selfdestruct(payable(msg.sender));
    }
    
    // MEDIUM: Public function that should be restricted
    function setOwner(address newOwner) public {
        // No access control - anyone can become owner!
        owner = newOwner;
    }
    
    // HIGH: Unchecked arithmetic could overflow
    function addBonus(address user, uint256 bonus) public onlyOwner {
        // In older Solidity versions, this could overflow
        balances[user] = balances[user] + bonus;
    }
    
    // Get contract balance
    function getContractBalance() public view returns (uint256) {
        return address(this).balance;
    }
    
    // MEDIUM: Random number generation using block properties
    function luckyDraw() public view returns (uint256) {
        // Miners can manipulate this
        return uint256(keccak256(abi.encodePacked(
            block.timestamp,
            block.difficulty,
            msg.sender
        ))) % 100;
    }
    
    // Fallback to receive ETH
    receive() external payable {
        balances[msg.sender] += msg.value;
        totalLocked += msg.value;
    }
}
