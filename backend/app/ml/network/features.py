class NetworkFeatureExtractor:
    """Extracts numerical features from a network flow log (e.g., Zeek/Bro log or NetFlow)."""
    
    def extract_features(self, flow_data: dict) -> list:
        # In a real environment, this would parse PCAP or Zeek conn.log
        # Here we expect a dictionary with basic flow metrics
        
        # Example flow data expected:
        # {
        #   "duration": 0.5,
        #   "src_bytes": 1500,
        #   "dst_bytes": 5000,
        #   "missed_bytes": 0,
        #   "src_pkts": 10,
        #   "dst_pkts": 15,
        #   "protocol": "tcp"
        # }
        
        protocol_map = {"tcp": 0, "udp": 1, "icmp": 2}
        proto = protocol_map.get(flow_data.get("protocol", "tcp").lower(), 3)
        
        features = [
            float(flow_data.get("duration", 0.0)),
            float(flow_data.get("src_bytes", 0)),
            float(flow_data.get("dst_bytes", 0)),
            float(flow_data.get("missed_bytes", 0)),
            float(flow_data.get("src_pkts", 0)),
            float(flow_data.get("dst_pkts", 0)),
            float(proto)
        ]
        
        return features
