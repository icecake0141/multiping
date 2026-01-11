#!/usr/bin/env python3
"""
Unit tests for multiping functionality
"""

import unittest
from unittest.mock import patch, MagicMock, mock_open
import argparse
import sys
import os

# Add parent directory to path to import main
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import handle_options, read_input_file, ping_host, main


class TestHandleOptions(unittest.TestCase):
    """Test command line option parsing"""
    
    def test_default_options(self):
        """Test default option values"""
        with patch('sys.argv', ['main.py', 'example.com']):
            args = handle_options()
            self.assertEqual(args.timeout, 1)
            self.assertEqual(args.count, 4)
            self.assertEqual(args.verbose, False)
            self.assertEqual(args.hosts, ['example.com'])
    
    def test_custom_timeout(self):
        """Test custom timeout option"""
        with patch('sys.argv', ['main.py', '-t', '5', 'example.com']):
            args = handle_options()
            self.assertEqual(args.timeout, 5)
    
    def test_custom_count(self):
        """Test custom count option"""
        with patch('sys.argv', ['main.py', '-c', '10', 'example.com']):
            args = handle_options()
            self.assertEqual(args.count, 10)
    
    def test_verbose_flag(self):
        """Test verbose flag"""
        with patch('sys.argv', ['main.py', '-v', 'example.com']):
            args = handle_options()
            self.assertTrue(args.verbose)
    
    def test_multiple_hosts(self):
        """Test multiple hosts"""
        with patch('sys.argv', ['main.py', 'host1.com', 'host2.com', 'host3.com']):
            args = handle_options()
            self.assertEqual(len(args.hosts), 3)
            self.assertIn('host1.com', args.hosts)


class TestReadInputFile(unittest.TestCase):
    """Test input file reading functionality"""
    
    def test_read_valid_file(self):
        """Test reading a valid input file"""
        file_content = "host1.com\nhost2.com\nhost3.com\n"
        with patch('builtins.open', mock_open(read_data=file_content)):
            hosts = read_input_file('test.txt')
            self.assertEqual(len(hosts), 3)
            self.assertEqual(hosts, ['host1.com', 'host2.com', 'host3.com'])
    
    def test_read_file_with_comments(self):
        """Test reading file with comments"""
        file_content = "host1.com\n# This is a comment\nhost2.com\n"
        with patch('builtins.open', mock_open(read_data=file_content)):
            hosts = read_input_file('test.txt')
            self.assertEqual(len(hosts), 2)
            self.assertEqual(hosts, ['host1.com', 'host2.com'])
    
    def test_read_file_with_empty_lines(self):
        """Test reading file with empty lines"""
        file_content = "host1.com\n\nhost2.com\n\n"
        with patch('builtins.open', mock_open(read_data=file_content)):
            hosts = read_input_file('test.txt')
            self.assertEqual(len(hosts), 2)
            self.assertEqual(hosts, ['host1.com', 'host2.com'])
    
    def test_file_not_found(self):
        """Test handling of missing file"""
        with patch('builtins.open', side_effect=FileNotFoundError()):
            hosts = read_input_file('nonexistent.txt')
            self.assertEqual(hosts, [])
    
    def test_permission_denied(self):
        """Test handling of permission error"""
        with patch('builtins.open', side_effect=PermissionError()):
            hosts = read_input_file('restricted.txt')
            self.assertEqual(hosts, [])


class TestPingHost(unittest.TestCase):
    """Test ping host functionality"""
    
    @patch('main.ICMP')
    @patch('main.IP')
    @patch('main.sr')
    def test_ping_host_success(self, mock_sr, mock_ip, mock_icmp):
        """Test successful ping"""
        # Mock IP and ICMP packet creation
        mock_packet = MagicMock()
        mock_ip.return_value.__truediv__ = MagicMock(return_value=mock_packet)
        
        # Mock successful ping response - ans should be a truthy list
        mock_answer = MagicMock()
        mock_sr.return_value = ([mock_answer], [])
        
        host, success, total = ping_host('example.com', 1, 4, False)
        
        self.assertEqual(host, 'example.com')
        self.assertEqual(success, 4)
        self.assertEqual(total, 4)
    
    @patch('main.ICMP')
    @patch('main.IP')
    @patch('main.sr')
    def test_ping_host_failure(self, mock_sr, mock_ip, mock_icmp):
        """Test failed ping"""
        # Mock IP and ICMP packet creation
        mock_packet = MagicMock()
        mock_ip.return_value.__truediv__ = MagicMock(return_value=mock_packet)
        
        # Mock failed ping response (no answers)
        mock_sr.return_value = ([], [MagicMock()])
        
        host, success, total = ping_host('example.com', 1, 4, False)
        
        self.assertEqual(host, 'example.com')
        self.assertEqual(success, 0)
        self.assertEqual(total, 4)
    
    @patch('main.ICMP')
    @patch('main.IP')
    @patch('main.sr')
    def test_ping_host_partial_success(self, mock_sr, mock_ip, mock_icmp):
        """Test partial ping success"""
        # Mock IP and ICMP packet creation
        mock_packet = MagicMock()
        mock_ip.return_value.__truediv__ = MagicMock(return_value=mock_packet)
        
        # Mock alternating success/failure
        mock_answer = MagicMock()
        mock_sr.side_effect = [
            ([mock_answer], []),
            ([], [MagicMock()]),
            ([mock_answer], []),
            ([], [MagicMock()])
        ]
        
        host, success, total = ping_host('example.com', 1, 4, False)
        
        self.assertEqual(host, 'example.com')
        self.assertEqual(success, 2)
        self.assertEqual(total, 4)
    
    @patch('main.ICMP')
    @patch('main.IP')
    @patch('main.sr')
    def test_ping_host_with_network_error(self, mock_sr, mock_ip, mock_icmp):
        """Test ping with network error"""
        # Mock IP and ICMP packet creation
        mock_packet = MagicMock()
        mock_ip.return_value.__truediv__ = MagicMock(return_value=mock_packet)
        
        mock_sr.side_effect = OSError("Network unreachable")
        
        host, success, total = ping_host('example.com', 1, 2, False)
        
        self.assertEqual(host, 'example.com')
        self.assertEqual(success, 0)
        self.assertEqual(total, 2)


class TestMain(unittest.TestCase):
    """Test main function"""
    
    @patch('main.ThreadPoolExecutor')
    @patch('main.ping_host')
    def test_main_with_hosts(self, mock_ping, mock_executor):
        """Test main function with hosts"""
        args = argparse.Namespace(
            timeout=1,
            count=4,
            verbose=False,
            hosts=['host1.com', 'host2.com'],
            input=None
        )
        
        # Mock ping results
        mock_ping.return_value = ('host1.com', 4, 4)
        
        # Mock executor
        mock_future = MagicMock()
        mock_future.result.return_value = ('host1.com', 4, 4)
        mock_executor_instance = MagicMock()
        mock_executor_instance.__enter__.return_value.submit.return_value = mock_future
        mock_executor.return_value = mock_executor_instance
        
        # Should not raise exception
        main(args)
    
    @patch('builtins.print')
    def test_main_with_invalid_count(self, mock_print):
        """Test main function with invalid count"""
        args = argparse.Namespace(
            timeout=1,
            count=0,
            verbose=False,
            hosts=['host1.com'],
            input=None
        )
        
        main(args)
        mock_print.assert_called()
    
    @patch('builtins.print')
    def test_main_with_no_hosts(self, mock_print):
        """Test main function with no hosts"""
        args = argparse.Namespace(
            timeout=1,
            count=4,
            verbose=False,
            hosts=[],
            input=None
        )
        
        main(args)
        mock_print.assert_called()
    
    @patch('main.read_input_file')
    @patch('main.ThreadPoolExecutor')
    def test_main_with_input_file(self, mock_executor, mock_read_file):
        """Test main function with input file"""
        mock_read_file.return_value = ['host1.com', 'host2.com']
        
        args = argparse.Namespace(
            timeout=1,
            count=4,
            verbose=False,
            hosts=[],
            input='hosts.txt'
        )
        
        # Mock executor
        mock_future = MagicMock()
        mock_future.result.return_value = ('host1.com', 4, 4)
        mock_executor_instance = MagicMock()
        mock_executor_instance.__enter__.return_value.submit.return_value = mock_future
        mock_executor.return_value = mock_executor_instance
        
        main(args)
        mock_read_file.assert_called_once_with('hosts.txt')


if __name__ == '__main__':
    unittest.main()
