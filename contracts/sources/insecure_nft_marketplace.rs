use anchor_lang::prelude::*;
use anchor_spl::token::{self, Token, TokenAccount, Mint, MintTo, Transfer};

declare_id!("NFT1234567890123456789012345678901234567890");

/**
 * INTENTIONALLY VULNERABLE SOLANA NFT PROGRAM - FOR TESTING ONLY
 * 
 * This program demonstrates common Solana NFT vulnerabilities:
 * 1. Missing signer verification
 * 2. Unchecked arithmetic
 * 3. Panic-prone unwrap() calls
 * 4. Unsafe blocks without validation
 * 5. Missing account constraints
 */

#[program]
pub mod insecure_nft_marketplace {
    use super::*;

    // CRITICAL: Anyone can mint NFTs (no signer check on authority)
    pub fn mint_nft(
        ctx: Context<MintNFT>,
        metadata_uri: String,
    ) -> Result<()> {
        let nft = &mut ctx.accounts.nft_account;
        let mint = &ctx.accounts.mint;
        
        // HIGH: Unchecked arithmetic - can overflow
        nft.token_id = nft.token_id + 1;
        nft.owner = ctx.accounts.payer.key();
        nft.metadata_uri = metadata_uri;
        nft.price = 0;
        nft.listed = false;
        
        // Mint token - but authority isn't properly checked!
        let cpi_accounts = MintTo {
            mint: mint.to_account_info(),
            to: ctx.accounts.token_account.to_account_info(),
            authority: ctx.accounts.authority.to_account_info(),
        };
        let cpi_program = ctx.accounts.token_program.to_account_info();
        let cpi_ctx = CpiContext::new(cpi_program, cpi_accounts);
        
        token::mint_to(cpi_ctx, 1)?;
        
        Ok(())
    }
    
    // HIGH: Missing ownership verification
    pub fn list_nft(
        ctx: Context<ListNFT>,
        price: u64,
    ) -> Result<()> {
        let nft = &mut ctx.accounts.nft_account;
        
        // No check if caller actually owns the NFT!
        nft.price = price;
        nft.listed = true;
        
        Ok(())
    }
    
    // CRITICAL: Multiple vulnerabilities in buy function
    pub fn buy_nft(ctx: Context<BuyNFT>) -> Result<()> {
        let nft = &mut ctx.accounts.nft_account;
        let price = nft.price;
        
        // MEDIUM: unwrap() can panic
        let buyer_balance = ctx.accounts.buyer.lamports().checked_sub(price).unwrap();
        
        // HIGH: Unchecked arithmetic
        let seller_lamports = ctx.accounts.seller.lamports() + price;
        
        // CRITICAL: Direct lamport manipulation without proper checks
        **ctx.accounts.buyer.try_borrow_mut_lamports()? -= price;
        **ctx.accounts.seller.try_borrow_mut_lamports()? += price;
        
        // State updates
        nft.owner = ctx.accounts.buyer.key();
        nft.listed = false;
        nft.price = 0;
        
        Ok(())
    }
    
    // HIGH: Unsafe block without validation
    pub fn get_nft_metadata(ctx: Context<QueryNFT>) -> Result<String> {
        let nft_info = ctx.accounts.nft_account.to_account_info();
        
        // MEDIUM: Using unwrap
        let data = nft_info.try_borrow_data().unwrap();
        
        // HIGH: Unsafe pointer operations
        unsafe {
            let ptr = data.as_ptr().add(64); // Assume metadata starts at byte 64
            let len = *(ptr as *const u32) as usize;
            let str_ptr = ptr.add(4);
            let slice = std::slice::from_raw_parts(str_ptr, len);
            let metadata = String::from_utf8_unchecked(slice.to_vec());
            return Ok(metadata);
        }
    }
    
    // CRITICAL: No signer check - anyone can transfer any NFT
    pub fn transfer_nft(
        ctx: Context<TransferNFT>,
        new_owner: Pubkey,
    ) -> Result<()> {
        let nft = &mut ctx.accounts.nft_account;
        
        // No ownership verification!
        nft.owner = new_owner;
        nft.listed = false;
        
        // Transfer token
        let cpi_accounts = Transfer {
            from: ctx.accounts.from_token.to_account_info(),
            to: ctx.accounts.to_token.to_account_info(),
            authority: ctx.accounts.authority.to_account_info(),
        };
        let cpi_program = ctx.accounts.token_program.to_account_info();
        let cpi_ctx = CpiContext::new(cpi_program, cpi_accounts);
        
        token::transfer(cpi_ctx, 1)?;
        
        Ok(())
    }
    
    // MEDIUM: Integer overflow in royalty calculation
    pub fn calculate_royalties(
        ctx: Context<QueryNFT>,
        sale_price: u64,
        royalty_percentage: u64,
    ) -> Result<u64> {
        // No overflow protection!
        let royalty = (sale_price * royalty_percentage) / 100;
        Ok(royalty)
    }
    
    // HIGH: Unchecked array access
    pub fn batch_update_prices(
        ctx: Context<BatchUpdate>,
        prices: Vec<u64>,
    ) -> Result<()> {
        // MEDIUM: unwrap without error handling
        let mut nft_data = ctx.accounts.nft_account.try_borrow_mut_data().unwrap();
        
        // HIGH: No bounds checking!
        for (i, price) in prices.iter().enumerate() {
            let offset = i * 8;
            // Could write beyond array bounds
            unsafe {
                let ptr = nft_data.as_mut_ptr().add(offset);
                *(ptr as *mut u64) = *price;
            }
        }
        
        Ok(())
    }
}

// CRITICAL: Missing signer constraint on authority
#[derive(Accounts)]
pub struct MintNFT<'info> {
    #[account(init, payer = payer, space = 8 + 200)]
    pub nft_account: Account<'info, NFTMetadata>,
    
    #[account(mut)]
    pub mint: Account<'info, Mint>,
    
    #[account(mut)]
    pub token_account: Account<'info, TokenAccount>,
    
    #[account(mut)]
    pub payer: Signer<'info>,
    
    // CRITICAL: Should be a signer!
    /// CHECK: Authority not properly validated
    pub authority: AccountInfo<'info>,
    
    pub token_program: Program<'info, Token>,
    pub system_program: Program<'info, System>,
}

// MEDIUM: Missing constraints
#[derive(Accounts)]
pub struct ListNFT<'info> {
    #[account(mut)]
    pub nft_account: Account<'info, NFTMetadata>,
    
    // No verification that lister owns the NFT
    pub lister: Signer<'info>,
}

#[derive(Accounts)]
pub struct BuyNFT<'info> {
    #[account(mut)]
    pub nft_account: Account<'info, NFTMetadata>,
    
    #[account(mut)]
    pub buyer: Signer<'info>,
    
    /// CHECK: Seller account not validated
    #[account(mut)]
    pub seller: AccountInfo<'info>,
}

// CRITICAL: No signer on authority
#[derive(Accounts)]
pub struct TransferNFT<'info> {
    #[account(mut)]
    pub nft_account: Account<'info, NFTMetadata>,
    
    #[account(mut)]
    pub from_token: Account<'info, TokenAccount>,
    
    #[account(mut)]
    pub to_token: Account<'info, TokenAccount>,
    
    /// CHECK: Authority should be signer
    pub authority: AccountInfo<'info>,
    
    pub token_program: Program<'info, Token>,
}

#[derive(Accounts)]
pub struct QueryNFT<'info> {
    pub nft_account: Account<'info, NFTMetadata>,
}

// MEDIUM: No constraints on who can batch update
#[derive(Accounts)]
pub struct BatchUpdate<'info> {
    #[account(mut)]
    pub nft_account: Account<'info, NFTMetadata>,
    
    pub caller: Signer<'info>,
}

#[account]
pub struct NFTMetadata {
    pub token_id: u64,
    pub owner: Pubkey,
    pub metadata_uri: String,
    pub price: u64,
    pub listed: bool,
    pub royalty_percentage: u8,
}
