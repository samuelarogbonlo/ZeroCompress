#!/usr/bin/env python3
"""
Tests for the transaction collector module
"""

import os
import sys
import unittest
import json
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scripts.transaction_collector import TransactionCollector, NETWORK_CONFIGS

class TestTransactionCollector(unittest.TestCase):
    """Test cases for the TransactionCollector class"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_output_dir = os.path.join(os.path.dirname(__file__), 'test_output')
        os.makedirs(self.test_output_dir, exist_ok=True)
    
    def tearDown(self):
        """Clean up after tests"""
        # Optionally remove test files created during tests
        pass
    
    @patch('scripts.transaction_collector.Web3')
    def test_initialization(self, mock_web3):
        """Test that the collector initializes correctly"""
        # Mock web3 connection
        mock_web3.return_value.is_connected.return_value = True
        mock_web3.return_value.eth.chain_id = NETWORK_CONFIGS['arbitrum']['chain_id']
        
        # Create collector
        collector = TransactionCollector('arbitrum', self.test_output_dir)
        
        # Check initialization
        self.assertEqual(collector.network, 'arbitrum')
        self.assertEqual(collector.chain_id, NETWORK_CONFIGS['arbitrum']['chain_id'])
        self.assertTrue(os.path.exists(os.path.join(self.test_output_dir, 'arbitrum')))
    
    @patch('scripts.transaction_collector.Web3')
    def test_process_transaction(self, mock_web3):
        """Test transaction processing logic"""
        # Mock web3 connection
        mock_web3.return_value.is_connected.return_value = True
        mock_web3.return_value.eth.chain_id = NETWORK_CONFIGS['arbitrum']['chain_id']
        
        # Create collector
        collector = TransactionCollector('arbitrum', self.test_output_dir)
        
        # Create mock tx and block
        mock_tx = {
            'hash': '0x123',
            'from': '0xabcdef1234567890abcdef1234567890abcdef12',
            'to': '0x1234567890abcdef1234567890abcdef12345678',
            'value': 1000000000000000000,  # 1 ETH
            'input': '0xa9059cbb0000000000000000000000001234567890abcdef1234567890abcdef1234567800000000000000000000000000000000000000000000000de0b6b3a7640000',
            'gas': 21000,
            'gasPrice': 20000000000,
            'nonce': 42,
            'blockNumber': 1234567
        }
        
        mock_block = MagicMock()
        mock_block.timestamp = 1625097600  # Example timestamp
        
        # Process transaction
        processed_tx = collector._process_transaction(mock_tx, mock_block)
        
        # Check basic processing
        self.assertEqual(processed_tx['hash'], '0x123')
        self.assertEqual(processed_tx['timestamp'], 1625097600)
        self.assertEqual(processed_tx['type'], 'erc20_transfer')  # Based on function signature
        
        # Check zero byte counting
        self.assertIn('zero_bytes', processed_tx)
        self.assertIn('zero_byte_percentage', processed_tx)
    
    @patch('scripts.transaction_collector.Web3')
    def test_classify_transaction(self, mock_web3):
        """Test transaction classification logic"""
        # Mock web3 connection
        mock_web3.return_value.is_connected.return_value = True
        mock_web3.return_value.eth.chain_id = NETWORK_CONFIGS['arbitrum']['chain_id']
        
        # Create collector
        collector = TransactionCollector('arbitrum', self.test_output_dir)
        
        # Test empty input (ETH transfer)
        self.assertEqual(collector._classify_transaction({'input': '0x'}), 'eth_transfer')
        
        # Test ERC20 transfer
        self.assertEqual(
            collector._classify_transaction({'input': '0xa9059cbb0000000000000000000000001234567890abcdef1234567890abcdef1234567800000000000000000000000000000000000000000000000de0b6b3a7640000'}), 
            'erc20_transfer'
        )
        
        # Test contract deployment
        self.assertEqual(
            collector._classify_transaction({'input': '0x6080604052...', 'to': None}),
            'contract_deployment'
        )
        
        # Test unknown function signature
        self.assertEqual(
            collector._classify_transaction({'input': '0xffffffff0000000000000000000000001234567890abcdef1234567890abcdef1234567800000000000000000000000000000000000000000000000de0b6b3a7640000', 'to': '0x1234'}),
            'contract_interaction'
        )

if __name__ == '__main__':
    unittest.main() 