import { useState, useEffect } from "react";
import { Card, Switch, Form, InputNumber, Select, Button, message, Divider, Typography } from "antd";
import { useTranslation } from "react-i18next";
import api from "../../../api";
import styles from "./index.module.less";

const { Option } = Select;
const { Title } = Typography;

interface SandboxConfig {
  enabled: boolean;
  type: string;
  timeout: number;
  max_memory: number | null;
  max_cpu: number | null;
}

export default function SandboxConfigPage() {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(false);
  const [config, setConfig] = useState<SandboxConfig>({
    enabled: true,
    type: "base",
    timeout: 60,
    max_memory: null,
    max_cpu: null,
  });

  // 加载配置
  useEffect(() => {
    const loadConfig = async () => {
      try {
        setLoading(true);
        const response = await api.getConfig();
        if (response) {
          setConfig({
            enabled: response.enabled,
            type: response.type,
            timeout: response.timeout,
            max_memory: response.max_memory,
            max_cpu: response.max_cpu,
          });
        }
      } catch (error) {
        message.error(t("sandboxConfig.loadError"));
      } finally {
        setLoading(false);
      }
    };

    loadConfig();
  }, [t]);

  // 保存配置
  const handleSave = async () => {
    try {
      setLoading(true);
      await api.updateConfig({ sandbox: config });
      message.success(t("sandboxConfig.saveSuccess"));
      
      // 如果启用了沙箱，尝试启动沙箱服务
      if (config.enabled) {
        try {
          // 通过执行一个简单的命令来触发沙箱服务的启动
          await api.execute_shell_command("echo Sandbox service started");
          message.success(t("sandboxConfig.serviceStarted"));
        } catch (error) {
          console.log("Sandbox service startup attempt failed:", error);
          // 沙箱服务启动失败不影响配置保存
        }
      }
    } catch (error) {
      message.error(t("sandboxConfig.saveError"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      <Title level={2}>{t("sandboxConfig.title")}</Title>
      <Card className={styles.card}>
        <Form layout="vertical">
          <Form.Item
            label={t("sandboxConfig.enabled")}
            tooltip={t("sandboxConfig.enabledTooltip")}
          >
            <Switch
              checked={config.enabled}
              onChange={(checked) => setConfig({ ...config, enabled: checked })}
            />
          </Form.Item>

          <Divider />

          <Form.Item
            label={t("sandboxConfig.type")}
            tooltip={t("sandboxConfig.typeTooltip")}
          >
            <Select
              value={config.type}
              onChange={(value) => setConfig({ ...config, type: value })}
              style={{ width: "200px" }}
            >
              <Option value="base">{t("sandboxConfig.typeBase")}</Option>
              <Option value="filesystem">{t("sandboxConfig.typeFilesystem")}</Option>
            </Select>
          </Form.Item>

          <Form.Item
            label={t("sandboxConfig.timeout")}
            tooltip={t("sandboxConfig.timeoutTooltip")}
          >
            <InputNumber
              value={config.timeout}
              onChange={(value) => setConfig({ ...config, timeout: value || 60 })}
              min={1}
              max={300}
              style={{ width: "200px" }}
            />
            <span className={styles.unit}>{t("sandboxConfig.seconds")}</span>
          </Form.Item>

          <Form.Item
            label={t("sandboxConfig.maxMemory")}
            tooltip={t("sandboxConfig.maxMemoryTooltip")}
          >
            <InputNumber
              value={config.max_memory}
              onChange={(value) => setConfig({ ...config, max_memory: value || null })}
              min={1}
              max={8192}
              style={{ width: "200px" }}
            />
            <span className={styles.unit}>{t("sandboxConfig.mb")}</span>
            <div className={styles.helper}>{t("sandboxConfig.leaveEmpty")}</div>
          </Form.Item>

          <Form.Item
            label={t("sandboxConfig.maxCpu")}
            tooltip={t("sandboxConfig.maxCpuTooltip")}
          >
            <InputNumber
              value={config.max_cpu}
              onChange={(value) => setConfig({ ...config, max_cpu: value || null })}
              min={0.1}
              max={1.0}
              step={0.1}
              style={{ width: "200px" }}
            />
            <div className={styles.helper}>{t("sandboxConfig.leaveEmpty")}</div>
          </Form.Item>

          <Form.Item>
            <Button type="primary" onClick={handleSave} loading={loading}>
              {t("common.save")}
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}
