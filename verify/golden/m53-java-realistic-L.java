package com.example;

import java.util.List;

// Service facade
public class Greeter {
    private static final String TAG = "greeter";

    public String greet(String name) {
        if (name == null) {
            return "hello anonymous";
        }
        // trailing note
        return "hello " + name;
    }
}
