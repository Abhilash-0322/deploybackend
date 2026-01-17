// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * INTENTIONALLY VULNERABLE NFT CONTRACT - FOR TESTING ONLY
 * 
 * This contract demonstrates common NFT vulnerabilities:
 * 1. Missing access controls
 * 2. tx.origin authentication
 * 3. Unsafe external calls
 * 4. Integer manipulation risks
 */

contract InsecureNFTMarketplace {
    struct NFT {
        uint256 tokenId;
        address owner;
        uint256 price;
        bool forSale;
        string uri;
    }
    
    mapping(uint256 => NFT) public nfts;
    mapping(address => uint256[]) public userNFTs;
    
    uint256 public nextTokenId;
    address public admin;
    uint256 public platformFee = 250; // 2.5% in basis points
    
    event NFTMinted(uint256 indexed tokenId, address indexed owner);
    event NFTListed(uint256 indexed tokenId, uint256 price);
    event NFTSold(uint256 indexed tokenId, address from, address to, uint256 price);
    
    constructor() {
        admin = msg.sender;
        nextTokenId = 1;
    }
    
    // CRITICAL: Using tx.origin instead of msg.sender
    modifier onlyAdmin() {
        require(tx.origin == admin, "Not admin");
        _;
    }
    
    // HIGH: No access control - anyone can mint
    function mintNFT(string memory uri) public returns (uint256) {
        uint256 tokenId = nextTokenId;
        
        nfts[tokenId] = NFT({
            tokenId: tokenId,
            owner: msg.sender,
            price: 0,
            forSale: false,
            uri: uri
        });
        
        userNFTs[msg.sender].push(tokenId);
        nextTokenId++;
        
        emit NFTMinted(tokenId, msg.sender);
        return tokenId;
    }
    
    // MEDIUM: Missing ownership verification
    function listNFT(uint256 tokenId, uint256 price) public {
        // Should verify msg.sender owns the NFT!
        nfts[tokenId].price = price;
        nfts[tokenId].forSale = true;
        
        emit NFTListed(tokenId, price);
    }
    
    // CRITICAL: Reentrancy + tx.origin vulnerability
    function buyNFT(uint256 tokenId) public payable {
        NFT storage nft = nfts[tokenId];
        require(nft.forSale, "NFT not for sale");
        require(msg.value >= nft.price, "Insufficient payment");
        
        address seller = nft.owner;
        uint256 price = nft.price;
        
        // Calculate fees
        uint256 fee = (price * platformFee) / 10000;
        uint256 sellerAmount = price - fee;
        
        // CRITICAL: External calls before state changes
        // MEDIUM: Using send() which can fail silently
        payable(seller).send(sellerAmount);
        payable(admin).send(fee);
        
        // State updates after external calls (reentrancy risk)
        nft.owner = msg.sender;
        nft.forSale = false;
        nft.price = 0;
        
        // Update user mappings
        _removeFromUserNFTs(seller, tokenId);
        userNFTs[msg.sender].push(tokenId);
        
        emit NFTSold(tokenId, seller, msg.sender, price);
        
        // Refund excess payment
        if (msg.value > price) {
            // HIGH: Using transfer for refund
            payable(msg.sender).transfer(msg.value - price);
        }
    }
    
    // CRITICAL: Delegatecall to arbitrary address
    function executeCustomLogic(address logic, bytes memory data) public onlyAdmin {
        // Allows admin to execute arbitrary code in contract's context
        (bool success, ) = logic.delegatecall(data);
        require(success, "Execution failed");
    }
    
    // HIGH: Unprotected state modification
    function transferNFT(uint256 tokenId, address to) public {
        // No ownership check!
        address from = nfts[tokenId].owner;
        
        nfts[tokenId].owner = to;
        nfts[tokenId].forSale = false;
        
        _removeFromUserNFTs(from, tokenId);
        userNFTs[to].push(tokenId);
    }
    
    // MEDIUM: Public function should be restricted
    function setAdmin(address newAdmin) public {
        // Anyone can call this!
        admin = newAdmin;
    }
    
    // MEDIUM: Timestamp-based logic
    function isEligibleForDiscount(address user) public view returns (bool) {
        // Using block.timestamp for time-based decisions
        uint256 accountAge = block.timestamp - 1704067200; // Jan 1, 2024
        return accountAge > 30 days && userNFTs[user].length > 0;
    }
    
    // Helper function
    function _removeFromUserNFTs(address user, uint256 tokenId) private {
        uint256[] storage tokens = userNFTs[user];
        for (uint256 i = 0; i < tokens.length; i++) {
            if (tokens[i] == tokenId) {
                tokens[i] = tokens[tokens.length - 1];
                tokens.pop();
                break;
            }
        }
    }
    
    // CRITICAL: Selfdestruct without proper access control
    function closeMarketplace() public {
        // Uses tx.origin check which can be bypassed
        require(tx.origin == admin, "Not admin");
        selfdestruct(payable(admin));
    }
    
    // Get user's NFT count
    function getUserNFTCount(address user) public view returns (uint256) {
        return userNFTs[user].length;
    }
}
