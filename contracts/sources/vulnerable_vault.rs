use anchor_lang::prelude::*;
use anchor_spl::token::{self, Token, TokenAccount, Transfer};

declare_id!("VuLn1234567890123456789012345678901234567890");

/**
 * INTENTIONALLY VULNERABLE SOLANA VAULT - FOR TESTING ONLY
 * 
 * This program contains critical Solana/Rust vulnerabilities:
 * 1. Missing signer checks
 * 2. Unchecked arithmetic operations
 * 3. Unsafe unwrap() calls
 * 4. Missing account ownership validation
 * 5. Missing constraint checks
 */

#[program]
pub mod vulnerable_vault {
    use super::*;

    // CRITICAL: Missing signer validation!
    // Anyone can call this function to withdraw from any vault
    pub fn withdraw(ctx: Context<Withdraw>, amount: u64) -> Result<()> {
        let vault = &mut ctx.accounts.vault;
        
        // HIGH: Unchecked arithmetic - can underflow!
        vault.balance = vault.balance - amount;
        
        // Transfer tokens without proper authorization
        let cpi_accounts = Transfer {
            from: ctx.accounts.vault_token.to_account_info(),
            to: ctx.accounts.user_token.to_account_info(),
            authority: ctx.accounts.authority.to_account_info(),
        };
        let cpi_program = ctx.accounts.token_program.to_account_info();
        let cpi_ctx = CpiContext::new(cpi_program, cpi_accounts);
        
        token::transfer(cpi_ctx, amount)?;
        
        Ok(())
    }
    
    // MEDIUM: Using unwrap() which can panic
    pub fn get_user_balance(ctx: Context<Query>) -> Result<u64> {
        let data = ctx.accounts.user_account.to_account_info();
        
        // MEDIUM: unwrap() will panic if borrow fails
        let account_data = data.try_borrow_data().unwrap();
        
        // HIGH: Unsafe pointer arithmetic
        unsafe {
            let ptr = account_data.as_ptr();
            let balance = *(ptr as *const u64);
            return Ok(balance);
        }
    }
    
    // HIGH: Missing account ownership validation
    pub fn update_authority(ctx: Context<UpdateAuth>, new_authority: Pubkey) -> Result<()> {
        let vault = &mut ctx.accounts.vault;
        
        // No check if caller is current authority!
        vault.authority = new_authority;
        
        Ok(())
    }
    
    // HIGH: Unchecked arithmetic in deposit
    pub fn deposit(ctx: Context<Deposit>, amount: u64) -> Result<()> {
        let vault = &mut ctx.accounts.vault;
        
        // HIGH: Can overflow!
        vault.balance = vault.balance + amount;
        vault.total_deposits = vault.total_deposits + 1;
        
        let cpi_accounts = Transfer {
            from: ctx.accounts.user_token.to_account_info(),
            to: ctx.accounts.vault_token.to_account_info(),
            authority: ctx.accounts.user.to_account_info(),
        };
        let cpi_program = ctx.accounts.token_program.to_account_info();
        let cpi_ctx = CpiContext::new(cpi_program, cpi_accounts);
        
        token::transfer(cpi_ctx, amount)?;
        
        Ok(())
    }
    
    // CRITICAL: No signer check and unsafe operations
    pub fn emergency_drain(ctx: Context<Emergency>) -> Result<()> {
        let vault = &mut ctx.accounts.vault;
        let amount = vault.balance;
        
        // MEDIUM: Using unwrap on Result
        let data = ctx.accounts.vault.to_account_info().try_borrow_mut_data().unwrap();
        
        // HIGH: Unsafe memory manipulation
        unsafe {
            let ptr = data.as_mut_ptr();
            std::ptr::write_bytes(ptr, 0, 8); // Zero out balance
        }
        
        // Transfer all funds
        let cpi_accounts = Transfer {
            from: ctx.accounts.vault_token.to_account_info(),
            to: ctx.accounts.destination.to_account_info(),
            authority: ctx.accounts.authority.to_account_info(),
        };
        let cpi_program = ctx.accounts.token_program.to_account_info();
        let cpi_ctx = CpiContext::new(cpi_program, cpi_accounts);
        
        token::transfer(cpi_ctx, amount)?;
        
        Ok(())
    }
    
    // HIGH: Integer overflow in reward calculation
    pub fn calculate_rewards(ctx: Context<Query>, multiplier: u64) -> Result<u64> {
        let vault = &ctx.accounts.vault;
        
        // No overflow checking!
        let rewards = vault.balance * multiplier;
        
        Ok(rewards)
    }
}

// MEDIUM: Mutable account without proper constraints
#[derive(Accounts)]
pub struct Withdraw<'info> {
    #[account(mut)]
    pub vault: Account<'info, Vault>,
    
    #[account(mut)]
    pub vault_token: Account<'info, TokenAccount>,
    
    #[account(mut)]
    pub user_token: Account<'info, TokenAccount>,
    
    // Should be a signer but isn't marked!
    pub authority: AccountInfo<'info>,
    
    pub token_program: Program<'info, Token>,
}

#[derive(Accounts)]
pub struct Deposit<'info> {
    #[account(mut)]
    pub vault: Account<'info, Vault>,
    
    #[account(mut)]
    pub vault_token: Account<'info, TokenAccount>,
    
    #[account(mut)]
    pub user_token: Account<'info, TokenAccount>,
    
    pub user: Signer<'info>,
    pub token_program: Program<'info, Token>,
}

#[derive(Accounts)]
pub struct Emergency<'info> {
    #[account(mut)]
    pub vault: Account<'info, Vault>,
    
    #[account(mut)]
    pub vault_token: Account<'info, TokenAccount>,
    
    #[account(mut)]
    pub destination: Account<'info, TokenAccount>,
    
    // CRITICAL: No signer constraint!
    pub authority: AccountInfo<'info>,
    
    pub token_program: Program<'info, Token>,
}

// MEDIUM: Missing constraints on authority field
#[derive(Accounts)]
pub struct UpdateAuth<'info> {
    #[account(mut)]
    pub vault: Account<'info, Vault>,
    
    // Should check if caller is current authority
    pub caller: Signer<'info>,
}

#[derive(Accounts)]
pub struct Query<'info> {
    pub vault: Account<'info, Vault>,
    
    /// CHECK: This account is not validated
    pub user_account: AccountInfo<'info>,
}

#[account]
pub struct Vault {
    pub balance: u64,
    pub authority: Pubkey,
    pub total_deposits: u64,
    pub created_at: i64,
}
