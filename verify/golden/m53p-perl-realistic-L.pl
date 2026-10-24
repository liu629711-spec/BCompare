#!/usr/bin/perl
# main program

=pod
Documentation block
=cut

sub greet {
    my ($name) = @_;
    return "hello $name";
}

print greet("world");
