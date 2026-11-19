# IOS-XE system logging

- **Cisco RS-Cookbook IOS-XE logging recipe**:
  <https://wwwin-github.cisco.com/gct-dp/RS-Cookbook/blob/master/Config%20Recipes/IOS-XE/logging.cisco>.
  Accessed 2026-11-19. The recipe includes `logging buffered informational`
  and `logging on` for local system-message logging.
- **Cisco IOS XE System Message Guide**:
  <https://www.cisco.com/c/en/us/td/docs/ios-xml/ios/17_xe/syslogs/17-13-x/b-system-message-guide-17-13-x.html>.
  System messages identify the facility, severity, mnemonic, and description.
- **Cisco service timestamps command reference**:
  <https://www.cisco.com/E-Learning/bulk/public/tac/cim/cib/using_cisco_ios_software/cmdrefs/service_timestamps.htm>.
  Accessed 2026-11-19. Documents `service timestamps log datetime msec`
  and its dependence on the system clock.
- **Cisco IP Security VPN Monitoring**:
  <https://www.cisco.com/c/en/us/td/docs/ios-xml/ios/sec_conn_imgmt/configuration/xe-16-12/sec-ipsec-management-xe-16-12-book/sec-ip-security-vpn.html>.
  Documents example crypto-session up and down messages at severity 5.

Verify platform and release support, logging status, and representative VPN
events on the target device. The configuration is not evidence that every
relevant event is emitted, retained, or delivered to a collector.
