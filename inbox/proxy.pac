function FindProxyForURL(url, host) {
    // 遇到局域网请求直接直连
    if (isPlainHostName(host) ||
        shExpMatch(host, "*.local") ||
        isInNet(host, "10.0.0.0", "255.0.0.0") ||
        isInNet(host, "172.16.0.0", "255.240.0.0") ||
        isInNet(host, "192.168.0.0", "255.255.0.0") ||
        isInNet(host, "127.0.0.0", "255.255.255.0")) {
        return "DIRECT";
    }
    // 默认将流量转发给手机节点
    return "PROXY 192.168.10.99:10808; DIRECT";
}
