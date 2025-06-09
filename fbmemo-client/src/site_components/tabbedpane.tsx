import React, { useState } from "react";

// Example subtab content component
const SubTabContent = ({ number }: { number: number }) => <div>SubTab {number} content.</div>;

const TabContent = ({ number }: { number: number }) => <div>Tab {number} content.</div>;

const initialTabs = [
  { id: "Tab1", label: "Tab 1", color: "#ef4444", component: <TabContent number={1} /> },
];

const initialSubTabs = {
  Tab1: [
    { id: "SubTab1", label: "SubTab 1", component: <SubTabContent number={1} /> }
  ]
};

const TabbedPane = () => {
  const [tabs, setTabs] = useState(initialTabs);
  const [activeTab, setActiveTab] = useState(tabs[0].id);
  const [tabCount, setTabCount] = useState(1);

  // Subtabs state: { [tabId]: Array<subtab> }
  const [subTabs, setSubTabs] = useState<{ [tabId: string]: any[] }>(initialSubTabs);
  const [activeSubTab, setActiveSubTab] = useState<{ [tabId: string]: string }>({ Tab1: "SubTab1" });
  const [subTabCount, setSubTabCount] = useState<{ [tabId: string]: number }>({ Tab1: 1 });

  // Add a new tab
  const addTab = () => {
    const newTabNumber = tabCount + 1;
    const newId = `Tab${newTabNumber}`;
    const colors = ["#ef4444", "#f59e42", "#3b82f6", "#22c55e", "#a21caf"];
    setTabs([
      ...tabs,
      {
        id: newId,
        label: `Tab ${newTabNumber}`,
        color: colors[(tabCount) % colors.length],
        component: <TabContent number={newTabNumber} />
      }
    ]);
    setActiveTab(newId);
    setTabCount(newTabNumber);

    // Initialize subtabs for new tab
    setSubTabs({
      ...subTabs,
      [newId]: [
        { id: "SubTab1", label: "SubTab 1", component: <SubTabContent number={1} /> }
      ]
    });
    setActiveSubTab({ ...activeSubTab, [newId]: "SubTab1" });
    setSubTabCount({ ...subTabCount, [newId]: 1 });

  };

  // Add a new subtab for the active tab
  const addSubTab = (tabId: string) => {
    const count = (subTabCount[tabId] || 1) + 1;
    const newSubTabId = `SubTab${count}`;
    const newSubTab = {
      id: newSubTabId,
      label: `SubTab ${count}`,
      component: <SubTabContent number={count} />
    };
    setSubTabs({
      ...subTabs,
      [tabId]: [...(subTabs[tabId] || []), newSubTab]
    });
    setActiveSubTab({ ...activeSubTab, [tabId]: newSubTabId });
    setSubTabCount({ ...subTabCount, [tabId]: count });
  };

  // Remove a subtab
  const removeSubTab = (tabId: string, subTabId: string) => {
    const filtered = (subTabs[tabId] || []).filter(st => st.id !== subTabId);
    setSubTabs({ ...subTabs, [tabId]: filtered });
    if (activeSubTab[tabId] === subTabId && filtered.length > 0) {
      setActiveSubTab({ ...activeSubTab, [tabId]: filtered[0].id });
    }
  };

  return (
    <div>
      {/* Tab Headers */}
      <div style={{ display: "flex", borderBottom: "2px solid #ccc" }}>
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              padding: "10px 20px",
              cursor: "pointer",
              border: "none",
              backgroundColor: tab.color,
              borderBottom: activeTab === tab.id ? "2px solid blue" : "none",
              fontWeight: activeTab === tab.id ? "bold" : "normal",
              color: "#fff",
              marginRight: "4px",
              position: "relative"
            }}
          >
            {tab.label}
          </button>
        ))}
        <button onClick={addTab} style={{ marginLeft: 8, padding: "10px 20px" }}>+</button>
      </div>

      {/* Tab Content */}
      <div style={{ padding: "20px", border: "1px solid #ccc" }}>
        {tabs.find(tab => tab.id === activeTab)?.component}

        {/* SubTab Headers */}
        <div style={{ display: "flex", marginTop: "16px", borderBottom: "1px solid #eee" }}>
          {(subTabs[activeTab] || []).map((subTab) => (
            <button
              key={subTab.id}
              onClick={() => setActiveSubTab({ ...activeSubTab, [activeTab]: subTab.id })}
              style={{
                padding: "6px 14px",
                cursor: "pointer",
                border: "none",
                backgroundColor: activeSubTab[activeTab] === subTab.id ? "#3b82f6" : "#e5e7eb",
                color: activeSubTab[activeTab] === subTab.id ? "#fff" : "#111",
                marginRight: "4px",
                borderRadius: "4px",
                fontWeight: activeSubTab[activeTab] === subTab.id ? "bold" : "normal",
                position: "relative"
              }}
            >
              {subTab.label}
              {(subTabs[activeTab] || []).length > 1 && (
                <span
                  onClick={e => {
                    e.stopPropagation();
                    removeSubTab(activeTab, subTab.id);
                  }}
                  style={{
                    marginLeft: 8,
                    color: "#fff",
                    cursor: "pointer",
                    fontWeight: "bold",
                    position: "absolute",
                    right: 6,
                    top: 2
                  }}
                >
                  ×
                </span>
              )}
            </button>
          ))}
          <button onClick={() => addSubTab(activeTab)} style={{ marginLeft: 8, padding: "6px 14px" }}>+</button>
        </div>

        {/* SubTab Content */}
        <div style={{ padding: "12px" }}>
          {(subTabs[activeTab] || []).find(st => st.id === activeSubTab[activeTab])?.component}
        </div>
      </div>
    </div>
  );
};

export default TabbedPane;