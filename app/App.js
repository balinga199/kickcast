import React, { useEffect, useState, useCallback } from "react";
import {
  SafeAreaView, FlatList, Text, View, ActivityIndicator,
  RefreshControl, StatusBar, StyleSheet,
} from "react-native";

const URL =
  "https://raw.githubusercontent.com/BALINGA/KICKCAST/main/data/predictions.json";

export default function App() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    try {
      const res = await fetch(URL + "?t=" + Date.now());
      setData(await res.json());
      setError(null);
    } catch (e) {
      setError("Could not load predictions.");
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const onRefresh = async () => {
    setRefreshing(true);
    await load();
    setRefreshing(false);
  };

  const renderItem = ({ item }) => (
    <View style={s.card}>
      <Text style={s.date}>{item.date} {item.time}</Text>
      <Text style={s.teams}>{item.home} vs {item.away}</Text>
      <View style={s.bar}>
        <View style={[s.seg, { flex: item.p_home, backgroundColor: "#2e7d32" }]} />
        <View style={[s.seg, { flex: item.p_draw, backgroundColor: "#9e9e9e" }]} />
        <View style={[s.seg, { flex: item.p_away, backgroundColor: "#1565c0" }]} />
      </View>
      <Text style={s.probs}>
        {Math.round(item.p_home * 100)}% / {Math.round(item.p_draw * 100)}% / {Math.round(item.p_away * 100)}%
      </Text>
      <Text style={s.pick}>
        Prediction: {item.pick} ({Math.round(item.confidence * 100)}%)
      </Text>
    </View>
  );

  return (
    <SafeAreaView style={s.container}>
      <StatusBar barStyle="light-content" />
      <Text style={s.title}>KickCast</Text>
      <Text style={s.sub}>Statistical predictions, not betting tips</Text>
      {!data && !error && <ActivityIndicator size="large" color="#fff" />}
      {error && <Text style={s.err}>{error}</Text>}
      {data && (
        <FlatList
          data={data.predictions}
          keyExtractor={(_, i) => String(i)}
          renderItem={renderItem}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#fff" />}
          ListEmptyComponent={<Text style={s.err}>No upcoming fixtures right now.</Text>}
        />
      )}
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#0f1720", paddingTop: 40 },
  title: { color: "#fff", fontSize: 28, fontWeight: "bold", marginLeft: 16 },
  sub: { color: "#90a4ae", marginLeft: 16, marginBottom: 12 },
  card: { backgroundColor: "#1c2733", margin: 10, marginTop: 0, padding: 14, borderRadius: 12 },
  date: { color: "#90a4ae", fontSize: 12 },
  teams: { color: "#fff", fontSize: 18, fontWeight: "600", marginVertical: 6 },
  bar: { flexDirection: "row", height: 8, borderRadius: 4, overflow: "hidden" },
  seg: { height: 8 },
  probs: { color: "#b0bec5", fontSize: 12, marginTop: 4 },
  pick: { color: "#fff", fontWeight: "600", marginTop: 6 },
  err: { color: "#ef9a9a", textAlign: "center", margin: 20 },
});
